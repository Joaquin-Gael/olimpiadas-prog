from django.db import models
from api.users.models import Users

class ActiveManager(models.Manager):
    """
    Manager personalizado que filtra solo los objetos activos (is_active=True)
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)