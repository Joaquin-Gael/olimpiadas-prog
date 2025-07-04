"""
Vistas para manejo de órdenes
"""
from typing import List, Optional
from django.http import HttpRequest
from django.core.exceptions import ValidationError
from ninja import Router

from .models import Orders, Sales
from .schemas import (
    OrderListOut, OrderCancelIn,
    PaymentMethodIn, PaymentOut, PaymentStatusOut,
    RefundIn, RefundOut, ErrorResponse, SuccessResponse,
    OrderFilterIn, SaleOut, SaleSummaryOut
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

router = Router(tags=["orders"])


@router.post(
    "/orders/{order_id}/pay",
    response={200: PaymentOut, 400: ErrorResponse, 409: ErrorResponse, 500: ErrorResponse},
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
            'card_number': payload.card_number,
            'expiry_date': payload.expiry_date,
            'cvv': payload.cvv,
            'cardholder_name': payload.cardholder_name
        }
        
        # Procesar el pago
        sale = PaymentService.process_payment(
            order_id=order_id,
            payment_method=payload.payment_method,
            payment_data=payment_data,
            idempotency_key=idemp_key
        )
        
        # Enviar notificación de confirmación de pago
        OrderNotificationService.send_payment_confirmation(sale)
        
        return 200, PaymentOut(
            sale_id=sale.id,
            transaction_id=sale.transaction_id,
            amount=float(sale.amount),
            payment_status=sale.payment_status,
            order_id=sale.order.id,
            payment_method=sale.payment_method,
            created_at=sale.created_at
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
        queryset = Orders.objects.filter(client=request.user)
        
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