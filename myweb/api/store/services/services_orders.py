"""
Servicios para manejo de órdenes de compra
"""
from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.utils import timezone

from ..models import Cart, Orders, OrderDetails, OrderState, CartStatus
from api.core.notification.services import NotificationService
from api.products.models import ProductsMetadata, ComponentPackages


class InvalidCartStateError(Exception):
    """El carrito no está en estado válido para crear orden."""

class OrderCreationError(Exception):
    """Error al crear la orden."""


@transaction.atomic
def create_order_from_cart(cart_id: int, user_id: int, idempotency_key: str):
    """
    Crea una orden desde un carrito existente.
    
    Args:
        cart_id: ID del carrito
        user_id: ID del usuario
        idempotency_key: Clave de idempotencia
        
    Returns:
        Orders: La orden creada
        
    Raises:
        InvalidCartStateError: Si el carrito no es válido
        OrderCreationError: Si hay error al crear la orden
    """
    cart = (Cart.objects
            .select_for_update()
            .prefetch_related("items")
            .get(id=cart_id, user_id=user_id, status=CartStatus.OPEN))
    
    if not cart.items_cnt:
        raise InvalidCartStateError("EMPTY_CART")
    
    order = Orders.objects.create(
        user_id=user_id,
        date=timezone.now(),
        state=OrderState.PENDING,
        total=cart.total,
        idempotency_key=idempotency_key,
    )
    
    # ✅ SOLUCIÓN: Mapear product_metadata a package_id usando ComponentPackages
    # Ahora package puede ser None para productos individuales
    product_metadata_ids = [li.product_metadata for li in cart.items.all()]
    component_map = {
        cp.product_metadata: cp.package_id
        for cp in ComponentPackages.objects.filter(
            product_metadata_id__in=product_metadata_ids
        )
    }
    
    OrderDetails.objects.bulk_create([
        OrderDetails(
            order=order,
            product_metadata_id=li.product_metadata.id,
            package_id=component_map.get(li.product_metadata),  # ✅ Puede ser None
            availability_id=li.availability_id,
            quantity=li.qty,
            unit_price=li.unit_price,
            subtotal=li.qty * li.unit_price,
            discount_applied=Decimal("0.00"),
        ) for li in cart.items.all()
    ])
    
    # ✅ SOLUCIÓN: Cambiar estado del carrito a ORDERED para evitar reutilización
    cart.status = CartStatus.ORDERED
    cart.save()
    
    NotificationService.booking_pending(order)
    return order


def cancel_order(order_id: int, user_id: int):
    """
    Cancela una orden.
    
    Args:
        order_id: ID de la orden
        user_id: ID del usuario
        
    Returns:
        Orders: La orden cancelada
    """
    with transaction.atomic():
        order = Orders.objects.select_for_update().get(
            id=order_id, user_id=user_id
        )
        
        if order.state not in [OrderState.PENDING, OrderState.CONFIRMED]:
            raise InvalidCartStateError("No se puede cancelar esta orden")
        
        order.state = OrderState.CANCELLED
        order.save()
        
        return order


def pay_order(order_id: int, user_id: int, payment_method: str):
    """
    Marca una orden como pagada.
    
    Args:
        order_id: ID de la orden
        user_id: ID del usuario
        payment_method: Método de pago
        
    Returns:
        Orders: La orden pagada
    """
    with transaction.atomic():
        order = Orders.objects.select_for_update().get(
            id=order_id, user_id=user_id
        )
        
        if order.state != OrderState.PENDING:
            raise InvalidCartStateError("La orden no está pendiente de pago")
        
        order.state = OrderState.CONFIRMED
        order.save()
        
        return order


def refund_order(order_id: int, user_id: int, amount: Optional[Decimal] = None):
    """
    Reembolsa una orden.
    
    Args:
        order_id: ID de la orden
        user_id: ID del usuario
        amount: Monto a reembolsar (si es None, reembolsa todo)
        
    Returns:
        Orders: La orden reembolsada
    """
    with transaction.atomic():
        order = Orders.objects.select_for_update().get(
            id=order_id, user_id=user_id
        )
        
        if order.state not in [OrderState.CONFIRMED, OrderState.COMPLETED]:
            raise InvalidCartStateError("No se puede reembolsar esta orden")
        
        order.state = OrderState.REFUNDED
        order.save()
        
        return order 

#  ─────────────────────────────────────────────────────────────
#  Clase pública – wrapper estático
#  ─────────────────────────────────────────────────────────────

class OrderService:
    """Fachada estática para que las vistas usen un API OO."""

    # get_order_by_id ----------------------------------------------------
    @staticmethod
    def get_order_by_id(order_id: int, user_id: int) -> "Orders | None":
        """Devuelve la orden si pertenece al usuario o None."""
        try:
            return Orders.objects.get(id=order_id, user_id=user_id)
        except Orders.DoesNotExist:
            return None

    # cancel_order -------------------------------------------------------
    @staticmethod
    def cancel_order(order_id: int, user_id: int) -> Orders:
        return cancel_order(order_id, user_id)

    # pay_order (alias; opcional) ----------------------------------------
    @staticmethod
    def pay_order(order_id: int, user_id: int, payment_method: str):
        return pay_order(order_id, user_id, payment_method)  # noqa: F821

    # refund_order -------------------------------------------------------
    @staticmethod
    def refund_order(order_id: int, user_id: int, amount: Optional[Decimal] = None):
        return refund_order(order_id, user_id, amount)  # noqa: F821 