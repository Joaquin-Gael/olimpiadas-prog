from asgiref.sync import sync_to_async

from pydantic import EmailStr

from api.core.notification.services import NotificationService

from ..models import Users

class UserNotificationsService:
    notification_service = NotificationService()
    @classmethod
    async def send_welcome(cls, email:EmailStr, user: Users):
        await sync_to_async(cls.notification_service.send_email)(
            template_name='welcome',
            to_email=email,
            context={ 'user_name': f'{user.first_name} {user.last_name}' },
            subject='¡Bienvenido!'
        )

    @classmethod
    async def send_recovery_password(cls, email: EmailStr, user: Users, reset_url: str):
        await sync_to_async(cls.notification_service.send_email)(
            template_name='password_reset',
            to_email=email,
            context={
                'user_name': f'{user.first_name} {user.last_name}',
                'reset_url': reset_url,
            },
            subject="Restablecer contraseña"
        )