"""
Servicios para notificaciones de órdenes
"""
from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import Order, Sale
from api.notification.services import NotificationService

User = get_user_model()


class OrderNotificationService:
    """Servicio para notificaciones relacionadas con órdenes"""
    
    @staticmethod
    def send_order_confirmation(order: Order) -> bool:
        """
        Envía confirmación de orden creada
        
        Args:
            order: La orden creada
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            context = {
                'order_id': order.id,
                'total': order.total,
                'user_name': order.user.get_full_name() or order.user.username,
                'user_email': order.user.email,
                'items_count': order.items.count(),
                'created_at': order.created_at.strftime('%d/%m/%Y %H:%M'),
            }
            
            return NotificationService.send_email(
                template_name='order_confirmation',
                to_email=order.user.email,
                context=context,
                subject='Confirmación de Orden'
            )
        except Exception as e:
            # Log error pero no fallar el flujo principal
            print(f"Error enviando confirmación de orden: {e}")
            return False
    
    @staticmethod
    def send_payment_confirmation(sale: Sale) -> bool:
        """
        Envía confirmación de pago exitoso
        
        Args:
            sale: La venta confirmada
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            context = {
                'order_id': sale.order.id,
                'sale_id': sale.id,
                'amount': sale.amount,
                'payment_method': sale.payment_method,
                'transaction_id': sale.transaction_id,
                'user_name': sale.order.user.get_full_name() or sale.order.user.username,
                'user_email': sale.order.user.email,
                'paid_at': sale.created_at.strftime('%d/%m/%Y %H:%M'),
            }
            
            return NotificationService.send_email(
                template_name='payment_confirmation',
                to_email=sale.order.user.email,
                context=context,
                subject='Confirmación de Pago'
            )
        except Exception as e:
            print(f"Error enviando confirmación de pago: {e}")
            return False
    
    @staticmethod
    def send_order_cancellation(order: Order, reason: Optional[str] = None) -> bool:
        """
        Envía notificación de cancelación de orden
        
        Args:
            order: La orden cancelada
            reason: Razón de la cancelación (opcional)
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            context = {
                'order_id': order.id,
                'total': order.total,
                'user_name': order.user.get_full_name() or order.user.username,
                'user_email': order.user.email,
                'cancelled_at': order.updated_at.strftime('%d/%m/%Y %H:%M'),
                'reason': reason or 'Cancelación solicitada por el usuario',
            }
            
            return NotificationService.send_email(
                template_name='order_cancellation',
                to_email=order.user.email,
                context=context,
                subject='Orden Cancelada'
            )
        except Exception as e:
            print(f"Error enviando notificación de cancelación: {e}")
            return False
    
    @staticmethod
    def send_payment_failed(order: Order, error_message: str) -> bool:
        """
        Envía notificación de pago fallido
        
        Args:
            order: La orden con pago fallido
            error_message: Mensaje de error del pago
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            context = {
                'order_id': order.id,
                'total': order.total,
                'user_name': order.user.get_full_name() or order.user.username,
                'user_email': order.user.email,
                'error_message': error_message,
                'failed_at': order.updated_at.strftime('%d/%m/%Y %H:%M'),
            }
            
            return NotificationService.send_email(
                template_name='payment_failed',
                to_email=order.user.email,
                context=context,
                subject='Pago Fallido'
            )
        except Exception as e:
            print(f"Error enviando notificación de pago fallido: {e}")
            return False
    
    @staticmethod
    def send_refund_confirmation(sale: Sale, refund_amount: Optional[float] = None) -> bool:
        """
        Envía confirmación de reembolso
        
        Args:
            sale: La venta reembolsada
            refund_amount: Monto reembolsado (si es parcial)
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            context = {
                'order_id': sale.order.id,
                'sale_id': sale.id,
                'original_amount': sale.amount,
                'refund_amount': refund_amount or sale.amount,
                'user_name': sale.order.user.get_full_name() or sale.order.user.username,
                'user_email': sale.order.user.email,
                'refunded_at': sale.updated_at.strftime('%d/%m/%Y %H:%M'),
                'is_partial': refund_amount is not None and refund_amount < sale.amount,
            }
            
            return NotificationService.send_email(
                template_name='refund_confirmation',
                to_email=sale.order.user.email,
                context=context,
                subject='Reembolso Procesado'
            )
        except Exception as e:
            print(f"Error enviando confirmación de reembolso: {e}")
            return False
    
    @staticmethod
    def send_order_reminder(order: Order) -> bool:
        """
        Envía recordatorio de orden pendiente de pago
        
        Args:
            order: La orden pendiente
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            context = {
                'order_id': order.id,
                'total': order.total,
                'user_name': order.user.get_full_name() or order.user.username,
                'user_email': order.user.email,
                'created_at': order.created_at.strftime('%d/%m/%Y %H:%M'),
                'hours_pending': int((timezone.now() - order.created_at).total_seconds() / 3600),
            }
            
            return NotificationService.send_email(
                template_name='order_reminder',
                to_email=order.user.email,
                context=context,
                subject='Recordatorio: Orden Pendiente de Pago'
            )
        except Exception as e:
            print(f"Error enviando recordatorio de orden: {e}")
            return False 