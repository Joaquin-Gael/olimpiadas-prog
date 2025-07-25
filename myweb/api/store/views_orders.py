"""
Vistas para manejo de órdenes
"""
from urllib.parse import urlencode

from typing import List, Optional
from django.http import HttpRequest, HttpResponseRedirect
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, reverse
from ninja import Router, Query
from ninja.errors import HttpError

from uuid import uuid4

from api.core.auth import SyncJWTBearer
from api.clients.models import Clients, IdentityDocumentType, Addresses, AddressType
#from whitenoise.responders import Redirect

from .idempotency import console
from .models import Orders, Sales
from .schemas import (
    OrderListOut, OrderCancelIn,
    PaymentMethodIn, PaymentOut, PaymentStatusOut,
    RefundIn, RefundOut, ErrorResponse, SuccessResponse,
    OrderFilterIn, SaleOut, SaleSummaryOut, StripeResponse
)
from .services import services_orders as order_srv
from .services.services_payments import PaymentService
from .services.services_notifications import OrderNotificationService
from .services.services_sales import SalesService

# ──────────────────────────────────────────────────────────────
# Helper común para la clave de idempotencia
# ──────────────────────────────────────────────────────────────


def get_idempotency_key(request) -> Optional[str]:
    """
    Devuelve la Idempotency-Key tomando cualquiera de los
    encabezados reconocidos:
        • Idempotency-Key               (estándar)
        • HTTP_IDEMPOTENCY_KEY          (Ninja TestClient)
    """
    return (
            request.headers.get("Idempotency-Key")
            or request.headers.get("HTTP_IDEMPOTENCY_KEY")
    )

router = Router(
    tags=["Orders"],
    auth=SyncJWTBearer()
)

public_router = Router(
    tags=["Orders"]
)

@public_router.get(
    "/pay/success",
    response={404: ErrorResponse, 500: ErrorResponse},
    summary="Verifica el estado de un pago exitoso"
)
def pay_success(request, session_id: str = Query(...), order_id: int = Query(...), payment_method: str = Query(...)):
    try:
        order = Orders.objects.get(id=order_id)

        payment_intent_id = PaymentService._get_payment_intent_id(session_id)

        if payment_intent_id is None:
            raise Exception("Payment intent not found")

        sale = PaymentService.create_sale(
            order=order,
            payment_method=payment_method,
            payment_intent_id=payment_intent_id,
            idempotency_key=str(uuid4())
        )

        try:
            _client = Clients.objects.filter(user_id=order.user_id).first()

        except Clients.DoesNotExist:
            Clients.objects.create(
                user=order.user,
                identity_document_type=IdentityDocumentType.DNI,
                identity_document="None",
                state=order.user.state
            )

        OrderNotificationService.send_payment_confirmation(sale, payment_method)

        result = PaymentOut(
            sale_id=sale.id,
            amount=float(sale.amount),
            payment_method=payment_method,
            payment_status=sale.payment_status,
            transaction_id=sale.transaction_id,
            created_at=sale.created_at,
            order_id=order_id,
        )

        return HttpResponseRedirect(f"/checkout/success?order_id={order_id}&session_id={session_id}")

    except Orders.DoesNotExist:
        return ErrorResponse(
            message="Orden no encontrada",
            error_code="ORDER_NOT_FOUND"
        )

    except Exception as e:
        return HttpError(status_code=500, message=str(e))

@public_router.get(
    "/pay/cancel",
    response={404:ErrorResponse, 500:ErrorResponse},
    summary="Verifica el estado de un pago canselado"
)
def pay_cancel(request, session_id: str = Query(...), order_id: int = Query(...)):
    try:
        order = Orders.objects.get(id=order_id)
        PaymentService.cancel_payment(order)

        paratemers = {
            "order_id": order_id,
            "session_id": session_id,
        }

        final_path = reverse("checkout_cancel") + "?" + urlencode(paratemers)

        return redirect(final_path)
        #return HttpResponseRedirect(f"/checkout/cancel?order_id={order_id}&session_id={session_id}")
    except Orders.DoesNotExist:
        return ErrorResponse(
            message="Orden no encontrada",
            error_code="ORDER_NOT_FOUND"
        )
    except Exception as e:
        return HttpError(status_code=500, message=str(e))

@router.post(
    "/{order_id}/pay",
    response={200: StripeResponse, 400: ErrorResponse, 409: ErrorResponse, 500: ErrorResponse},
)
def pay_order(request: HttpRequest, order_id: int, payload: PaymentMethodIn):
    """
    Procesa el pago de una orden
    """
    try:
        idemp_key = get_idempotency_key(request)
        if not idemp_key:
            return 409, ErrorResponse(          # 409 = "conflict" estilo Stripe
                message="Header Idempotency-Key es requerido",
                error_code="MISSING_IDEMPOTENCY_KEY",
            )

        # Preparar datos del pago
        payment_data = {
            'order_id': order_id,
        }

        # Procesar el pago
        session_url = PaymentService.process_payment(
            order_id=order_id,
            payment_method=payload.payment_method,
            payment_data=payment_data,
            idempotency_key=idemp_key
        )

        return {
            "session_url": session_url,
        }

    except ValidationError as e:
        return 400, ErrorResponse(
            message=str(e),
            error_code="VALIDATION_ERROR"
        )
    except Exception as e:
        console.print_exception(show_locals=True)
        return 500, ErrorResponse(
            message=f"Error interno: {str(e)}",
            error_code="INTERNAL_ERROR"
        )


@router.post("/orders/{order_id}/cancel", response={200: SuccessResponse, 400: ErrorResponse, 500: ErrorResponse})
def cancel_order(request: HttpRequest, order_id: int, payload: OrderCancelIn = None):
    """
    Cancela una orden
    """
    try:
        order = order_srv.OrderService.cancel_order(order_id, request.user.id)

        # Enviar notificación de cancelación
        reason = payload.reason if payload else None
        OrderNotificationService.send_order_cancellation(order, reason)

        return 200, SuccessResponse(
            message="Orden cancelada exitosamente",
            data={"order_id": order.id, "state": order.state}
        )

    except ValidationError as e:
        return 400, ErrorResponse(
            message=str(e),
            error_code="VALIDATION_ERROR"
        )
    except Exception as e:
        return 500, ErrorResponse(
            message=f"Error interno: {str(e)}",
            error_code="INTERNAL_ERROR"
        )


@router.get("/orders/", response={200: List[OrderListOut], 500: ErrorResponse})
def list_orders(request: HttpRequest, filters: OrderFilterIn = OrderFilterIn()):
    """
    Lista las órdenes del usuario
    """
    try:
        # Obtener órdenes del usuario con filtros
        queryset = Orders.objects.filter(user=request.user)

        if filters.state:
            queryset = queryset.filter(state=filters.state)

        if filters.start_date:
            queryset = queryset.filter(created_at__gte=filters.start_date)

        if filters.end_date:
            queryset = queryset.filter(created_at__lte=filters.end_date)

        orders = queryset.order_by('-created_at')[:filters.limit]

        return 200, [
            OrderListOut(
                id=order.id,
                total=float(order.total),
                state=order.state,
                created_at=order.created_at,
                client_id=order.client.id
            )
            for order in orders
        ]

    except Exception as e:
        return 500, ErrorResponse(
            message=f"Error interno: {str(e)}",
            error_code="INTERNAL_ERROR"
        )


@router.get("/orders/{order_id}/payment-status", response={200: PaymentStatusOut, 404: ErrorResponse, 500: ErrorResponse})
def get_payment_status(request: HttpRequest, order_id: int):
    """
    Obtiene el estado del pago de una orden
    """
    try:
        # Verificar que la orden existe y pertenece al usuario
        order = order_srv.OrderService.get_order_by_id(order_id, request.user.id)
        if not order:
            return 404, ErrorResponse(
                message="Orden no encontrada",
                error_code="ORDER_NOT_FOUND"
            )

        # Buscar la venta asociada
        try:
            sale = Sales.objects.get(order=order)
            return 200, PaymentStatusOut(
                order_id=order.id,
                payment_status=sale.payment_status,
                transaction_id=sale.transaction_id,
                amount=float(sale.amount),
                payment_method=sale.payment_method
            )
        except Sales.DoesNotExist:
            return 200, PaymentStatusOut(
                order_id=order.id,
                payment_status="PENDING",
                message="No se ha procesado ningún pago para esta orden"
            )

    except Exception as e:
        return 500, ErrorResponse(
            message=f"Error interno: {str(e)}",
            error_code="INTERNAL_ERROR"
        )


@router.post("/orders/{order_id}/refund", response={200: RefundOut, 400: ErrorResponse, 500: ErrorResponse})
def refund_order(request: HttpRequest, order_id: int, payload: RefundIn):
    """
    Procesa un reembolso para una orden
    """
    try:
        # Verificar que la orden existe y pertenece al usuario
        order = order_srv.OrderService.get_order_by_id(order_id, request.user.id)
        if not order:
            return 404, ErrorResponse(
                message="Orden no encontrada",
                error_code="ORDER_NOT_FOUND"
            )

        # Buscar la venta
        try:
            sale = Sales.objects.get(order=order)
        except Sales.DoesNotExist:
            return 400, ErrorResponse(
                message="No se encontró una venta para esta orden",
                error_code="SALE_NOT_FOUND"
            )

        # Procesar reembolso
        refunded_sale = PaymentService.refund_payment(
            sale_id=sale.id,
            amount=payload.amount
        )

        # Enviar notificación de reembolso
        OrderNotificationService.send_refund_confirmation(
            refunded_sale,
            refund_amount=payload.amount
        )

        return 200, RefundOut(
            message="Reembolso procesado exitosamente",
            sale_id=refunded_sale.id,
            refunded_amount=float(payload.amount or refunded_sale.amount)
        )

    except ValidationError as e:
        return 400, ErrorResponse(
            message=str(e),
            error_code="VALIDATION_ERROR"
        )
    except Exception as e:
        return 500, ErrorResponse(
            message=f"Error interno: {str(e)}",
            error_code="INTERNAL_ERROR"
        )


@router.get("/orders/{order_id}/sales", response={200: SaleOut, 404: ErrorResponse, 500: ErrorResponse})
def get_order_sale(request: HttpRequest, order_id: int):
    """
    Obtiene la venta asociada a una orden
    """
    try:
        # Verificar que la orden existe y pertenece al usuario
        order = order_srv.OrderService.get_order_by_id(order_id, request.user.id)
        if not order:
            return 404, ErrorResponse(
                message="Orden no encontrada",
                error_code="ORDER_NOT_FOUND"
            )

        # Buscar la venta
        try:
            sale = Sales.objects.get(order=order)
            return 200, SaleOut(
                id=sale.id,
                order_id=sale.order.id,
                amount=float(sale.amount),
                payment_method=sale.payment_method,
                payment_status=sale.payment_status,
                transaction_id=sale.transaction_id,
                created_at=sale.created_at
            )
        except Sales.DoesNotExist:
            return 404, ErrorResponse(
                message="No se encontró una venta para esta orden",
                error_code="SALE_NOT_FOUND"
            )

    except Exception as e:
        return 500, ErrorResponse(
            message=f"Error interno: {str(e)}",
            error_code="INTERNAL_ERROR"
        )


@router.get("/sales/summary", response={200: SaleSummaryOut, 500: ErrorResponse})
def get_sales_summary(request: HttpRequest):
    """
    Obtiene un resumen de ventas del usuario
    """
    try:
        summary = SalesService.get_sales_summary(request.user.id)

        return 200, SaleSummaryOut(
            total_sales=summary['total_sales'],
            total_amount=float(summary['total_amount']),
            recent_sales_count=summary['recent_sales_count'],
            recent_sales_amount=float(summary['recent_sales_amount']),
            average_amount=float(summary['average_amount'])
        )

    except Exception as e:
        return 500, ErrorResponse(
            message=f"Error interno: {str(e)}",
            error_code="INTERNAL_ERROR"
        )

orders_router = Router()
orders_router.add_router(router=public_router, prefix="")
orders_router.add_router(router=router, prefix="")