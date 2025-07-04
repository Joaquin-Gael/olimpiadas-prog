from django.core.mail import send_mail
from django.utils import timezone
from api.store.models import Notifications, NotificationType

def send_notification(order, notif_type: NotificationType, subject: str, body: str) -> None:
    Notifications.objects.create(
        order = order,
        email_destination = order.client.email,
        subject = subject,
        body = body,
        date = timezone.now(),
        notification_type = notif_type,
        shipping_state = order.state,
    )
    send_mail(subject, body, None, [order.client.email])

def send_notification_to_admin(notif_type: NotificationType, subject: str, body: str) -> None:
    raw_html = None