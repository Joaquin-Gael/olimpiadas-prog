"""
Servicio centralizado de notificaciones por email
"""
import logging
from typing import Dict, Any, Optional
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from api.store.models import Notifications, NotificationType

logger = logging.getLogger(__name__)


class NotificationService:
    """Servicio centralizado para envío de notificaciones"""
    
    @staticmethod
    def send_email(
        template_name: str,
        to_email: str,
        context: Dict[str, Any],
        subject: str,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Envía un email usando una plantilla
        
        Args:
            template_name: Nombre de la plantilla (sin extensión)
            to_email: Email del destinatario
            context: Contexto para la plantilla
            subject: Asunto del email
            from_email: Email remitente (opcional)
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Usar email por defecto si no se especifica
            if not from_email:
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@turismo.com')
            
            # Renderizar plantilla HTML
            html_template = f"emails/{template_name}.html"
            html_content = render_to_string(html_template, context)
            
            # Crear versión texto plano
            text_content = strip_tags(html_content)
            
            # Enviar email
            send_mail(
                subject=subject,
                message=text_content,
                from_email=from_email,
                recipient_list=[to_email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Email enviado exitosamente a {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email a {to_email}: {e}")
            return False
    
    @staticmethod
    def send_simple_email(
        to_email: str,
        subject: str,
        message: str,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Envía un email simple sin plantilla
        
        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            message: Mensaje del email
            from_email: Email remitente (opcional)
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            if not from_email:
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@turismo.com')
            
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[to_email],
                fail_silently=False
            )
            
            logger.info(f"Email simple enviado a {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email simple a {to_email}: {e}")
            return False
    
    @staticmethod
    def send_bulk_email(
        template_name: str,
        recipients: list,
        context: Dict[str, Any],
        subject: str,
        from_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía emails en lote
        
        Args:
            template_name: Nombre de la plantilla
            recipients: Lista de emails destinatarios
            context: Contexto para la plantilla
            subject: Asunto del email
            from_email: Email remitente (opcional)
            
        Returns:
            Dict con estadísticas del envío
        """
        if not from_email:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@turismo.com')
        
        success_count = 0
        failed_count = 0
        failed_emails = []
        
        for email in recipients:
            try:
                # Renderizar plantilla
                html_template = f"emails/{template_name}.html"
                html_content = render_to_string(html_template, context)
                text_content = strip_tags(html_content)
                
                # Enviar email
                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=from_email,
                    recipient_list=[email],
                    html_message=html_content,
                    fail_silently=False
                )
                
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_emails.append(email)
                logger.error(f"Error enviando email a {email}: {e}")
        
        result = {
            'total': len(recipients),
            'success': success_count,
            'failed': failed_count,
            'failed_emails': failed_emails
        }
        
        logger.info(f"Envio masivo completado: {result}")
        return result
    
    @staticmethod
    def send_order_confirmation_email(
        order_id: int,
        user_name: str,
        user_email: str,
        total: float,
        items_count: int,
        created_at: str
    ) -> bool:
        """
        Envía email de confirmación de orden (método específico)
        
        Args:
            order_id: ID de la orden
            user_name: Nombre del usuario
            user_email: Email del usuario
            total: Total de la orden
            items_count: Cantidad de items
            created_at: Fecha de creación
            
        Returns:
            bool: True si se envió exitosamente
        """
        context = {
            'order_id': order_id,
            'user_name': user_name,
            'total': total,
            'items_count': items_count,
            'created_at': created_at,
        }
        
        return NotificationService.send_email(
            template_name='emails/order_confirmation',
            to_email=user_email,
            context=context,
            subject=f'Confirmación de Orden #{order_id}'
        )
    
    @staticmethod
    def send_payment_confirmation_email(
        order_id: int,
        sale_id: int,
        user_name: str,
        user_email: str,
        amount: float,
        payment_method: str,
        transaction_id: str,
        paid_at: str
    ) -> bool:
        """
        Envía email de confirmación de pago (método específico)
        
        Args:
            order_id: ID de la orden
            sale_id: ID de la venta
            user_name: Nombre del usuario
            user_email: Email del usuario
            amount: Monto pagado
            payment_method: Método de pago
            transaction_id: ID de la transacción
            paid_at: Fecha del pago
            
        Returns:
            bool: True si se envió exitosamente
        """
        context = {
            'order_id': order_id,
            'sale_id': sale_id,
            'user_name': user_name,
            'amount': amount,
            'payment_method': payment_method,
            'transaction_id': transaction_id,
            'paid_at': paid_at,
        }
        
        return NotificationService.send_email(
            template_name='emails/payment_confirmation',
            to_email=user_email,
            context=context,
            subject=f'Confirmación de Pago - Orden #{order_id}'
        )
    
    @staticmethod
    def booking_pending(order):
        """
        Envía notificación de reserva pendiente
        
        Args:
            order: Instancia de Orders
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            context = {
                'order_id': order.id,
                'user_name': f"{order.user.first_name} {order.user.last_name}",
                'total': order.total,
                'created_at': order.date.strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            return NotificationService.send_email(
                template_name='booking_pending',
                to_email=order.user.email,
                context=context,
                subject=f'Reserva Pendiente - Orden #{order.id}'
            )
        except Exception as e:
            logger.error(f"Error enviando notificación de reserva pendiente para orden {order.id}: {e}")
            return False

def send_notification(order, notif_type: NotificationType, subject: str, body: str):
    Notifications.objects.create(
        order             = order,
        email_destination = order.client.email,
        subject           = subject,
        body              = body,
        date              = timezone.now(),
        notification_type = notif_type,
        shipping_state    = order.state,
    )
    send_mail(subject, body, None, [order.client.email])

def test_email_templates() -> None:
    # -----------------------
    # Envíos de prueba para cada template
    # -----------------------

    # Dummy classes para simulación de orden y usuario
    class DummyUser:
        def __init__(self):
            self.first_name = 'Test'
            self.last_name = 'User'
            self.email = 'guzmanantonio867@gmail.com'

    class DummyOrder:
        def __init__(self):
            self.id = 1
            self.user = DummyUser()
            self.total = 150.0
            self.date = timezone.now()

    dummy_order = DummyOrder()

    dummy_user = DummyUser()

    # 1. booking_pending
    NotificationService.booking_pending(dummy_order)

    # 2. order_confirmation
    NotificationService.send_order_confirmation_email(
        order_id=2,
        user_name='Test User',
        user_email=dummy_user.email,
        total=200.0,
        items_count=3,
        created_at=timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    # 3. password_reset
    NotificationService.send_email(
        template_name='password_reset',
        to_email=dummy_user.email,
        context={
            'user_name': 'Test User',
            'reset_link': 'https://example.com/reset?token=abc123'
        },
        subject='Restablecer contraseña'
    )

    # 4. payment_confirmation
    NotificationService.send_payment_confirmation_email(
        order_id=3,
        sale_id=101,
        user_name='Test User',
        user_email=dummy_user.email,
        amount=250.0,
        payment_method='Credit Card',
        transaction_id='txn_12345',
        paid_at=timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    # 5. welcome
    NotificationService.send_email(
        template_name='welcome',
        to_email=dummy_user.email,
        context={ 'user_name': 'Test User' },
        subject='¡Bienvenido!'
    )

    logger.info("Envíos de prueba completados.")