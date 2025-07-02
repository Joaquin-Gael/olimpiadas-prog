"""
Señales para la aplicación store.

Este módulo maneja la liberación automática de stock cuando las órdenes
cambian a estado CANCELLED o REFUNDED.
"""

from django.db.models.signals import pre_save
from django.db import transaction
from django.dispatch import receiver

from .models import Orders, OrderDetails
from api.products.services.stock_services import (
    release_activity, release_transportation,
    release_room_availability, release_flight,
    InsufficientStockError,
)

# Mapeo product_type → release_fn (el MISMO criterio que en carrito)
_RELEASE_MAP = {
    "activity":       release_activity,
    "transportation": release_transportation,
    "lodgment":       release_room_availability,
    "flight":         release_flight,
}

@receiver(pre_save, sender=Orders)
def orders_release_stock_on_cancel(sender, instance: Orders, **kwargs):
    """
    Si el estado de la orden cambió a CANCELLED liberamos stock.
    Se ejecuta dentro de una atomic de Django (pre_save).
    """
    # 1) Solo si es UPDATE (tiene pk) y va a CANCELLED o REFUNDED
    if not instance.pk:
        return

    try:
        previous = Orders.objects.get(pk=instance.pk)
    except Orders.DoesNotExist:
        return

    was_cancelled = previous.state in {"Cancelled", "Refunded"}
    will_cancel = instance.state in {"Cancelled", "Refunded"}
    
    if was_cancelled or not will_cancel:
        return

    # 2) Liberar stock por cada detalle – transacción implícita
    with transaction.atomic():
        for line in OrderDetails.objects.filter(order=instance):
            release_fn = _RELEASE_MAP.get(line.product_metadata.product_type)
            if not release_fn:
                continue  # producto no soportado aún

            try:
                release_fn(line.availability_id, line.quantity)
            except InsufficientStockError:
                # Ya estaba liberado → lo ignoramos para no frenar la cancel.
                pass 