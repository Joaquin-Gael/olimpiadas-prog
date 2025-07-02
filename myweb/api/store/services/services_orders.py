"""
Servicios de dominio para órdenes.

► Una única fuente de verdad para:
  • crear órdenes desde carritos
  • manejar estados de órdenes
  • validaciones de negocio

Cualquier vista (API / admin / tests) solo llama a estas funciones.
"""

from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from ..models import Orders, OrderDetails, Cart
from api.products.models import ProductsMetadata
from api.products.services.stock_services import (
    reserve_activity,       release_activity,
    reserve_transportation, release_transportation,
    reserve_room_availability, release_room_availability,
    reserve_flight,         release_flight,
    InsufficientStockError,
)

# ──────────────────────────────────────────────────────────────
# 1. EXCEPCIONES DE DOMINIO
# ──────────────────────────────────────────────────────────────

class OrderCreationError(Exception):
    """Error al crear la orden desde el carrito."""

class InvalidCartStateError(Exception):
    """El carrito no está en estado válido para crear orden."""

# ──────────────────────────────────────────────────────────────
# 2. MAPA PRODUCTO → FUNCIÓN DE STOCK
# ──────────────────────────────────────────────────────────────

_STOCK_MAP = {
    "activity":       (reserve_activity, release_activity),
    "transportation": (reserve_transportation, release_transportation),
    "lodgment":       (reserve_room_availability, release_room_availability),
    "flight":         (reserve_flight,   release_flight),
}

def _get_stock_funcs(product_type: str):
    """Devuelve (reserve_fn, release_fn) según product_type."""
    try:
        return _STOCK_MAP[product_type]
    except KeyError:  # producto todavía no soportado
        raise ValueError(f"Tipo de producto no soportado: {product_type}")

# ──────────────────────────────────────────────────────────────
# 3. API DE SERVICIO
# ──────────────────────────────────────────────────────────────

@transaction.atomic
def create_order_from_cart(cart: Cart) -> Orders:
    """
    Convierte un carrito en una orden formal con líneas de detalle.
    
    Pasos:
      1. Re-chequeo de stock (validación final)
      2. Crear encabezado de la orden
      3. Crear líneas de detalle (OrderDetails)
      4. Devolver la orden creada
    
    Args:
        cart: Carrito en estado OPEN con ítems
        
    Returns:
        Orders: La orden creada con sus detalles
        
    Raises:
        InvalidCartStateError: Si el carrito no está en estado OPEN
        InsufficientStockError: Si no hay stock suficiente para algún ítem
        OrderCreationError: Si falla la creación de la orden
    """
    if cart.status != "OPEN":
        raise InvalidCartStateError("El carrito debe estar en estado OPEN")
    
    if not cart.items.exists():
        raise OrderCreationError("El carrito no tiene ítems para procesar")
    
    # 1. Re-chequeo de stock (validación final)
    for line in cart.items.select_related(None):
        try:
            metadata = ProductsMetadata.objects.get(id=line.product_metadata_id)
            reserve_fn, _ = _get_stock_funcs(metadata.product_type)
            # qty = 0 significa "solo validar que existe y está activo"
            reserve_fn(line.availability_id, 0)
        except InsufficientStockError:
            raise InsufficientStockError(f"Stock insuficiente para el producto {line.product_metadata_id}")
        except Exception as e:
            raise OrderCreationError(f"Error validando stock: {str(e)}")
    
    # 2. Crear encabezado de la orden
    try:
        order = Orders.objects.create(
            client=cart.client,
            date=timezone.now(),
            state="Pending",  # Estado inicial según OrderTravelPackageStatus
            total=cart.total,
            address=cart.client.addresses.first(),  # Dirección por defecto del cliente
            notes="Generada desde checkout del carrito",
        )
    except Exception as e:
        raise OrderCreationError(f"Error creando encabezado de orden: {str(e)}")
    
    # 3. Crear líneas de detalle (OrderDetails)
    try:
        bulk_details = []
        for line in cart.items.all():
            metadata = ProductsMetadata.objects.get(id=line.product_metadata_id)
            
            # Buscar el paquete asociado (si existe)
            package = None
            if hasattr(metadata, 'package'):
                package = metadata.package
            
            bulk_details.append(OrderDetails(
                order=order,
                product_metadata=metadata,
                package=package,
                availability_id=line.availability_id,
                quantity=line.qty,
                unit_price=line.unit_price,
                subtotal=line.unit_price * line.qty,
                discount_applied=Decimal("0.00"),
            ))
        
        # Crear todas las líneas de una vez (más eficiente)
        OrderDetails.objects.bulk_create(bulk_details)
        
    except Exception as e:
        # Si falla la creación de detalles, la transacción se revierte automáticamente
        raise OrderCreationError(f"Error creando líneas de detalle: {str(e)}")
    
    return order 