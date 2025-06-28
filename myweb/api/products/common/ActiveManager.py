from django.db import models
from api.clients.models import Clients

class ActiveManager(models.Manager):
    """
    Manager personalizado que filtra solo los objetos activos (is_active=True)
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)