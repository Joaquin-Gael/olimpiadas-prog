"""
services_payments.py
Servicio de pagos con idempotencia, control de duplicados y simulación
de pasarela / reembolso.
"""
import stripe

import uuid
from decimal import Decimal
from typing import Dict, Any, Optional

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

from rich import console

from ..models import (
    Orders,
    Sales,
    OrderState,
    PaymentStatus,
    SaleType,
    PaymentType,
    OrderDetails
)

console = console.Console()

stripe.api_key = settings.STRIPE_KEY

DOMAIN = f"http://localhost:8080/"

# -------------------------------------------------------------------
#  Ayudas internas
# -------------------------------------------------------------------
def _next_transaction_number() -> int:
    """
    Genera el siguiente número de transacción (int) basado en la
    transacción más alta registrada.  Si tu base tiene una secuencia
    / trigger, podés omitir esto y delegar en la DB.
    """
    last = Sales.objects.order_by("-transaction_number").first()
    return (last.transaction_number if last else 0) + 1


# -------------------------------------------------------------------
#  Servicio principal
# -------------------------------------------------------------------
class PaymentService:
    """Capa de dominio para procesar cobros y reembolsos"""

    # ──────────────────────────────────────────────────────────
    #  Cobro / creación de venta
    # ──────────────────────────────────────────────────────────
    @staticmethod
    def process_payment(
        *,
        order_id: int,
        payment_method: str,
        payment_data: Dict[str, Any],
        idempotency_key: str,
    ):
        """
        Procesa el cobro de una orden garantizando idempotencia.

        - Bloquea la orden (`select_for_update`)
        - Verifica duplicados por orden e idempotency_key
        - Simula la pasarela
        - Crea la venta
        - Cambia estado de la orden a CONFIRMED
        """
        if not idempotency_key:
            raise ValidationError("MISSING_IDEMPOTENCY_KEY")

        with transaction.atomic():

            # 1) Obtener y bloquear la orden pendiente
            try:
                order = Orders.objects.select_for_update().get(
                    id=order_id,
                    state=OrderState.PENDING,
                )
                payment_data.setdefault("order", order)
            except Orders.DoesNotExist:
                raise ValidationError("Orden no encontrada o no válida para pago")

            # 2) Idempotencia
            #    a) ¿ya hay venta para la orden?
            if Sales.objects.filter(order=order).exists():
                raise ValidationError("La orden ya tiene un pago registrado")

            #    b) ¿ya se usó esta idempotency_key?
            sale_prev = Sales.objects.filter(idempotency_key=idempotency_key).first()
            if sale_prev:
                return sale_prev  # reintento seguro

            # 3) Llamar (mock) a la pasarela
            PaymentService._process_payment_with_gateway(
                amount=order.total,
                payment_method=payment_method,
                payment_data=payment_data,
            )

    @staticmethod
    def create_sale(
            order: Orders,
            payment_method: str,
            payment_intent_id: str,
            idempotency_key
    ) -> Sales | None:
        try:
            order.state = OrderState.IN_PROGRESS

            order.save()

            sale = Sales.objects.create(
                order=order,
                transaction_number=_next_transaction_number(),
                sale_date=timezone.now(),
                total=order.total,
                amount=order.total,
                payment_status=PaymentStatus.PAID_ONLINE,
                payment_method=payment_method,
                payment_type=PaymentType.ONLINE,
                sale_type=SaleType.ONLINE,
                transaction_id= payment_intent_id,
                idempotency_key=idempotency_key,
            )

            return sale
        except Exception as e:
            console.print_exception(show_locals=True)


    @staticmethod
    def cancel_payment(
            order: Orders
    ):
        try:
            order.state = OrderState.CANCELLED
            order.save()
        except Exception as e:
            console.print_exception(show_locals=True)


    @staticmethod
    def _get_payment_intent_id(session_id):
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session.payment_intent
        except Exception as e:
            console.print_exception(show_locals=True)
            return None

    # ──────────────────────────────────────────────────────────
    #  Reembolso
    # ──────────────────────────────────────────────────────────
    @staticmethod
    def refund_payment(
        *,
        sale_id: int,
        amount: Optional[Decimal] = None,
    ) -> Sales:
        """
        Reembolsa total o parcialmente una venta.

        - Bloquea la venta
        - Verifica que sea reembolsable
        - Simula la pasarela de reembolsos
        - Marca venta+orden como REFUNDED
        """
        with transaction.atomic():

            try:
                sale = Sales.objects.select_for_update().get(
                    id=sale_id,
                    payment_status=PaymentStatus.PAID_ONLINE,
                )
            except Sales.DoesNotExist:
                raise ValidationError("Venta no encontrada o no válida para reembolso")

            refund_amount = amount or sale.amount

            gw_refund = PaymentService._process_refund_with_gateway(
                transaction_id=sale.transaction_id,
                amount=refund_amount,
            )
            if not gw_refund["success"]:
                raise ValidationError(f"Reembolso rechazado: {gw_refund['message']}")

            # Actualizar venta
            sale.payment_status = PaymentStatus.REFUNDED
            sale.save(update_fields=["payment_status"])

            # Actualizar orden
            sale.order.state = OrderState.REFUNDED
            sale.order.save(update_fields=["state"])

            return sale

    # ──────────────────────────────────────────────────────────
    #  Helpers – Pasarela mock
    # ──────────────────────────────────────────────────────────
    @staticmethod
    def _process_payment_with_gateway(
        amount: Decimal,
        payment_method: str,
        payment_data: Dict[str, Any],
    ):
        """Simula validaciones básicas y genera un transaction_id."""

        detail_list: list[OrderDetails] = OrderDetails.objects.filter(order=payment_data.get("order"))

        line_items = []
        for detail in detail_list:
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(round(detail.product_metadata.unit_price*100)),
                    "product_data": {
                        "name": detail.product_metadata.name,
                        "images": [detail.product_metadata.image_url],
                    },
                },
                "quantity": detail.quantity,
            })

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=[payment_method],
                line_items=line_items,
                mode="payment",
                success_url=f"{DOMAIN}{settings.ID_PREFIX}/pay/success?session_id={{CHECKOUT_SESSION_ID}}&order_id={payment_data.get('order_id')}&payment_method={payment_method}",
                cancel_url=f"{DOMAIN}{settings.ID_PREFIX}/pay/cancel?order_id={payment_data.get('order_id')}",
            )
        except Exception as e:
            console.print_exception(show_locals=True)

    @staticmethod
    def _process_refund_with_gateway(
        transaction_id: str,
        amount: Decimal,
    ) -> Dict[str, Any]:
        """Mock de reembolso siempre exitoso."""
        return {
            "success": True,
            "refund_id": f"REF_{uuid.uuid4().hex[:16].upper()}",
            "message": "Reembolso procesado",
        }

    # ──────────────────────────────────────────────────────────
    #  Consulta de estado (helper simple)
    # ──────────────────────────────────────────────────────────
    @staticmethod
    def get_payment_status(sale_id: int) -> Optional[Sales]:
        return Sales.objects.filter(id=sale_id).first()
