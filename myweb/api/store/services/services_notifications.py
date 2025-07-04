"""
Servicios para notificaciones de órdenes
"""
from typing import Optional
import logging
from django.utils import timezone

from ..models import Orders, Sales
from api.core.notification.services import NotificationService

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────
#  Plantillas → (template_name, subject)
TPL_ORDER_CONF        = ("order_confirmation",    "Confirmación de Orden")
TPL_PAYMENT_CONF      = ("payment_confirmation",  "Confirmación de Pago")
TPL_ORDER_CANCEL      = ("order_cancellation",    "Orden Cancelada")
TPL_PAYMENT_FAILED    = ("payment_failed",        "Pago Fallido")
TPL_REFUND_CONF       = ("refund_confirmation",   "Reembolso Procesado")
TPL_ORDER_REMINDER    = ("order_reminder",        "Recordatorio: Orden Pendiente de Pago")
# ────────────────────────────────────────────────────────────────


class OrderNotificationService:
    """Envío de correos relacionados con órdenes"""

    # -----------------------------------------------------------
    @staticmethod
    def send_order_confirmation(order: Orders) -> bool:
        try:
            tpl, subj = TPL_ORDER_CONF
            context = {
                "order_id": order.id,
                "total": order.total,
                "user_name": order.client.get_full_name() or order.client.username,
                "user_email": order.client.email,
                "items_count": order.orderdetails_set.count(),
                "created_at": order.created_at.strftime("%d/%m/%Y %H:%M"),
            }
            return NotificationService.send_email(
                template_name=tpl, to_email=order.client.email,
                context=context, subject=subj
            )
        except Exception:
            logger.exception("Error enviando confirmación de orden")
            return False

    # -----------------------------------------------------------
    @staticmethod
    def send_payment_confirmation(sale: Sales) -> bool:
        try:
            tpl, subj = TPL_PAYMENT_CONF
            context = {
                "order_id": sale.order.id,
                "sale_id": sale.id,
                "amount": sale.amount,
                "payment_method": sale.payment_method,
                "transaction_id": sale.transaction_id,
                "user_name": sale.order.client.get_full_name() or sale.order.client.username,
                "user_email": sale.order.client.email,
                "paid_at": sale.created_at.strftime("%d/%m/%Y %H:%M"),
            }
            return NotificationService.send_email(
                template_name=tpl, to_email=sale.order.client.email,
                context=context, subject=subj
            )
        except Exception:
            logger.exception("Error enviando confirmación de pago")
            return False

    # -----------------------------------------------------------
    @staticmethod
    def send_order_cancellation(order: Orders, reason: Optional[str] = None) -> bool:
        try:
            tpl, subj = TPL_ORDER_CANCEL
            context = {
                "order_id": order.id,
                "total": order.total,
                "user_name": order.client.get_full_name() or order.client.username,
                "user_email": order.client.email,
                "cancelled_at": order.updated_at.strftime("%d/%m/%Y %H:%M"),
                "reason": reason or "Cancelación solicitada por el usuario",
            }
            return NotificationService.send_email(
                template_name=tpl, to_email=order.client.email,
                context=context, subject=subj
            )
        except Exception:
            logger.exception("Error enviando notificación de cancelación")
            return False

    # -----------------------------------------------------------
    @staticmethod
    def send_payment_failed(order: Orders, error_message: str) -> bool:
        try:
            tpl, subj = TPL_PAYMENT_FAILED
            context = {
                "order_id": order.id,
                "total": order.total,
                "user_name": order.client.get_full_name() or order.client.username,
                "user_email": order.client.email,
                "error_message": error_message,
                "failed_at": order.updated_at.strftime("%d/%m/%Y %H:%M"),
            }
            return NotificationService.send_email(
                template_name=tpl, to_email=order.client.email,
                context=context, subject=subj
            )
        except Exception:
            logger.exception("Error enviando notificación de pago fallido")
            return False

    # -----------------------------------------------------------
    @staticmethod
    def send_refund_confirmation(sale: Sales, refund_amount: Optional[float] = None) -> bool:
        try:
            tpl, subj = TPL_REFUND_CONF
            context = {
                "order_id": sale.order.id,
                "sale_id": sale.id,
                "original_amount": sale.amount,
                "refund_amount": refund_amount or sale.amount,
                "user_name": sale.order.client.get_full_name() or sale.order.client.username,
                "user_email": sale.order.client.email,
                "refunded_at": sale.updated_at.strftime("%d/%m/%Y %H:%M"),
                "is_partial": refund_amount is not None and refund_amount < sale.amount,
            }
            return NotificationService.send_email(
                template_name=tpl, to_email=sale.order.client.email,
                context=context, subject=subj
            )
        except Exception:
            logger.exception("Error enviando confirmación de reembolso")
            return False

    # -----------------------------------------------------------
    @staticmethod
    def send_order_reminder(order: Orders) -> bool:
        try:
            tpl, subj = TPL_ORDER_REMINDER
            context = {
                "order_id": order.id,
                "total": order.total,
                "user_name": order.client.get_full_name() or order.client.username,
                "user_email": order.client.email,
                "created_at": order.created_at.strftime("%d/%m/%Y %H:%M"),
                "hours_pending": int((timezone.now() - order.created_at).total_seconds() / 3600),
            }
            return NotificationService.send_email(
                template_name=tpl, to_email=order.client.email,
                context=context, subject=subj
            )
        except Exception:
            logger.exception("Error enviando recordatorio de orden")
            return False
