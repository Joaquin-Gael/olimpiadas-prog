"""
Servicios de dominio del carrito.

► Una única fuente de verdad para:
  • agregar / quitar ítems
  • actualizar cantidades
  • recalcular totales
  • expirar carritos
  • pasar de carrito a orden (checkout)

Cualquier vista (API / admin / tests) solo llama a estas funciones.
"""

from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone

from ..models import Cart, CartItem
from api.products.models import ProductsMetadata, Packages, ComponentPackages
from api.products.services.stock_services import (
    reserve_activity,       release_activity,
    reserve_transportation, release_transportation,
    reserve_room_availability, release_room_availability,
    reserve_flight,         release_flight,
    InsufficientStockError,
)

from rich.console import Console
console = Console()

# ──────────────────────────────────────────────────────────────
# 1. EXCEPCIONES DE DOMINIO
# ──────────────────────────────────────────────────────────────

class CartClosedError(Exception):
    """El carrito no está en estado OPEN."""

class CurrencyMismatchError(Exception):
    """La moneda del ítem no coincide con la del carrito."""

class PackageNotFoundError(Exception):
    """El paquete no existe o no está activo."""

class PackageComponentsError(Exception):
    """Error al procesar los componentes del paquete."""

# ──────────────────────────────────────────────────────────────
# 2. MAPA PRODUCTO → FUNCIÓN DE STOCK
# ──────────────────────────────────────────────────────────────

_STOCK_MAP = {
    "activity":       (reserve_activity, release_activity),
    "transportation": (reserve_transportation, release_transportation),
    "lodgment":       (reserve_room_availability, release_room_availability),
    "flight":         (reserve_flight,   release_flight),
    "flights":        (reserve_flight,   release_flight),
    "lodgments":      (reserve_room_availability, release_room_availability),
    "activities":     (reserve_activity, release_activity),
}

def _get_stock_funcs(product_type: str):
    """Devuelve (reserve_fn, release_fn) según product_type."""
    try:
        return _STOCK_MAP[product_type]
    except KeyError:  # producto todavía no soportado
        raise ValueError(f"Tipo de producto no soportado: {product_type}")

# ──────────────────────────────────────────────────────────────
# 3. AYUDAS PRIVADAS
# ──────────────────────────────────────────────────────────────

def _recalculate_cart(cart: Cart):
    """Re-evalúa totales y contador de ítems."""
    price_expr = models.ExpressionWrapper(
        models.F("qty") * models.F("unit_price"),
        output_field=models.DecimalField(max_digits=12, decimal_places=2)
    )
    agg = cart.items.aggregate(
        items_cnt=models.Sum("qty"),
        total=models.Sum(price_expr),
    )
    console.print(agg)
    cart.items_cnt = agg["items_cnt"] or 0
    cart.total     = (agg["total"] or Decimal("0.00")).quantize(Decimal("0.01"))
    cart.updated_at = timezone.now()
    cart.save(update_fields=["items_cnt", "total", "updated_at"])

# ──────────────────────────────────────────────────────────────
# 4. API DE SERVICIO
# ──────────────────────────────────────────────────────────────

@transaction.atomic
def add_item(
    cart: Cart,
    metadata: ProductsMetadata,
    availability_id: int | None,
    qty: int,
    unit_price: Decimal,
    config: dict | None = None,
) -> CartItem:
    """
    Añade (o acumula) un ítem al carrito.

    • Reserva cupos → si falla levanta `InsufficientStockError`.
    • Suma qty si la línea ya existía.
    • Actualiza totales del carrito.
    """
    if cart.status != "OPEN":
        raise CartClosedError("El carrito no está abierto")

    if cart.currency != metadata.currency:
        raise CurrencyMismatchError("La moneda del ítem no coincide con la del carrito")

    if qty <= 0:
        raise ValueError("qty debe ser positivo")

    reserve_fn, _ = _get_stock_funcs(metadata.product_type)

    console.print(f"product_type: {metadata.product_type} | availability_id: {availability_id} | qty: {qty} | unit_price: {unit_price} | config: {config}")
    console.print(f"Product Object: {metadata.get_content_object}")

    # 1) Reservar stock
    if metadata.product_type in ["flights", "flight"] or availability_id is None:
        _object = metadata.get_content_object
        reserve_fn(_object.id, qty)
    else:
        reserve_fn(availability_id, qty)

    # 2) Insertar o actualizar línea
    try:
        old_item = CartItem.objects.get(cart=cart, availability_id=availability_id, product_metadata_id=metadata.id)

        #item, created = CartItem.objects.select_for_update().get_or_create(
        #    cart=cart,
        #    availability_id=availability_id,
        #    product_metadata=metadata,
        #    defaults=dict(
        #        qty=qty,
        #        unit_price=unit_price,
        #        currency=metadata.currency,
        #        config=config or {},
        #    ),
        #)
        old_item.qty += qty
        old_item.save(update_fields=["qty", "updated_at"])

        _recalculate_cart(cart)
        console.print("Item already exists, updated qty")
        return old_item
    except CartItem.DoesNotExist:
        console.print_exception(show_locals=True)
        item = CartItem.objects.create(
            cart=cart,
            availability_id=availability_id,
            product_metadata=metadata,
            qty=qty,
            unit_price=metadata.unit_price,
            currency=metadata.currency,
            config=config or {},
        )
        _recalculate_cart(cart)
        return item

    # 3) Recalcular totales


@transaction.atomic
def add_package(
    cart: Cart,
    package_id: int,
    qty: int,
    config: dict | None = None,
) -> list[CartItem]:
    """
    Añade un paquete completo al carrito.
    
    • Valida que el paquete existe y está activo
    • Obtiene todos los componentes del paquete
    • Reserva stock para cada componente
    • Crea items en el carrito para cada componente
    • Actualiza totales del carrito
    
    Args:
        cart: Instancia del carrito
        package_id: ID del paquete a agregar
        qty: Cantidad de paquetes a agregar
        config: Configuración adicional del paquete
        
    Returns:
        List[CartItem]: Lista de items creados en el carrito
        
    Raises:
        PackageNotFoundError: Si el paquete no existe o no está activo
        PackageComponentsError: Si hay error al procesar componentes
        CartClosedError: Si el carrito no está abierto
        InsufficientStockError: Si no hay stock suficiente
    """
    if cart.status != "OPEN":
        raise CartClosedError("El carrito no está abierto")
    
    if qty <= 0:
        raise ValueError("qty debe ser positivo")
    
    # 1) Validar que el paquete existe y está activo
    try:
        package = Packages.objects.get(id=package_id, is_active=True)
    except Packages.DoesNotExist:
        raise PackageNotFoundError(f"Paquete {package_id} no encontrado o inactivo")
    
    # 2) Obtener componentes del paquete ordenados
    components = ComponentPackages.objects.filter(
        package=package
    ).select_related('product_metadata').order_by('order')
    
    if not components.exists():
        raise PackageComponentsError(f"Paquete {package_id} no tiene componentes")
    
    # 3) Validar moneda del paquete
    package_currency = package.currency if hasattr(package, 'currency') else 'USD'
    if cart.currency != package_currency:
        raise CurrencyMismatchError(f"Moneda del paquete ({package_currency}) no coincide con la del carrito ({cart.currency})")
    
    created_items = []
    
    try:
        # 4) Procesar cada componente del paquete
        for component in components:
            metadata = component.product_metadata
            
            # Validar que el metadata está activo
            if not metadata.is_active:
                raise PackageComponentsError(f"Componente {metadata.id} del paquete no está activo")
            
            # Calcular cantidad total para este componente
            component_qty = qty * (component.quantity or 1)
            
            # Determinar availability_id según el tipo de producto
            availability_id = None
            if hasattr(component, 'available_id') and component.available_id:
                availability_id = component.available_id
            
            # 5) Reservar stock para el componente
            reserve_fn, _ = _get_stock_funcs(metadata.product_type)
            
            if metadata.product_type in ["flights", "flight"] or availability_id is None:
                product_object = metadata.get_content_object
                reserve_fn(product_object.id, component_qty)
            else:
                reserve_fn(availability_id, component_qty)
            
            # 6) Crear o actualizar item en el carrito
            try:
                existing_item = CartItem.objects.get(
                    cart=cart, 
                    availability_id=availability_id, 
                    product_metadata=metadata
                )
                # Actualizar cantidad existente
                existing_item.qty += component_qty
                existing_item.save(update_fields=["qty", "updated_at"])
                created_items.append(existing_item)
                console.print(f"Item existente actualizado: {existing_item.id}")
                
            except CartItem.DoesNotExist:
                # Crear nuevo item
                item = CartItem.objects.create(
                    cart=cart,
                    availability_id=availability_id,
                    product_metadata=metadata,
                    qty=component_qty,
                    unit_price=metadata.unit_price,
                    currency=metadata.currency,
                    config=config or {},
                )
                created_items.append(item)
                console.print(f"Nuevo item creado: {item.id}")
        
        # 7) Recalcular totales del carrito
        _recalculate_cart(cart)
        
        return created_items
        
    except (InsufficientStockError, PackageComponentsError, CartClosedError):
        # Si hay error, liberar stock reservado
        for component in components:
            try:
                metadata = component.product_metadata
                component_qty = qty * (component.quantity or 1)
                availability_id = getattr(component, 'available_id', None)
                
                release_fn, _ = _get_stock_funcs(metadata.product_type)
                
                if metadata.product_type in ["flights", "flight"] or availability_id is None:
                    product_object = metadata.get_content_object
                    release_fn(product_object.id, component_qty)
                else:
                    release_fn(availability_id, component_qty)
            except Exception as e:
                console.print(f"Error liberando stock: {e}")
        
        # Re-lanzar la excepción original
        raise


# ──────────────────────────────────────────────────────────────
# 5. FUNCIONES DE STOCK
# ──────────────────────────────────────────────────────────────

@transaction.atomic
def update_qty(item: CartItem, new_qty: int):
    """
    Cambia la cantidad de un CartItem.

    • Si sube → reserva la diferencia.
    • Si baja → libera la diferencia.
    """
    if item.cart.status != "OPEN":
        raise CartClosedError("El carrito no está abierto")
    if new_qty <= 0:
        raise ValueError("new_qty debe ser positivo")

    diff = new_qty - item.qty
    if diff == 0:
        return item  # sin cambios

    # ✅ OPTIMIZACIÓN: Obtener product_type en una sola consulta
    metadata = ProductsMetadata.objects.get(id=item.product_metadata.id)
    reserve_fn, release_fn = _get_stock_funcs(metadata.product_type)

    # Reservar o liberar según el signo
    if diff > 0:
        reserve_fn(item.availability_id, diff)
    else:
        release_fn(item.availability_id, abs(diff))

    item.qty = new_qty
    item.save(update_fields=["qty", "updated_at"])
    _recalculate_cart(item.cart)
    return item


@transaction.atomic
def remove_item(item: CartItem, cart: Cart):
    """
    Elimina una línea del carrito y libera todo su stock.
    """
    try:
        if item.cart.status != "OPEN":
            console.print(item.cart.status)
            console.print(item.cart.id)
            raise CartClosedError("El carrito no está abierto")

        # ✅ OPTIMIZACIÓN: Obtener product_type en una sola consulta
        metadata = ProductsMetadata.objects.get(id=item.product_metadata.id)
        _, release_fn = _get_stock_funcs(metadata.product_type)

        release_fn(item.availability_id, item.qty)
        #cart = item.cart   # guardamos antes de borrar
        item.delete()
        _recalculate_cart(cart)
    except CartItem.DoesNotExist:
        pass
    finally:
        _recalculate_cart(cart)

@transaction.atomic
def expire_cart(cart: Cart):
    """
    Libera stock de un carrito y lo marca como EXPIRED.
    Se usa en el job de limpieza.
    """
    if cart.status != "OPEN":
        return  # nada que hacer

    # ✅ OPTIMIZACIÓN: Obtener todos los product_types en una sola consulta
    items_with_metadata = cart.items.select_for_update().select_related('product_metadata')
    
    for item in items_with_metadata:
        _, release_fn = _get_stock_funcs(item.product_metadata.product_type)
        release_fn(item.availability_id, item.qty)

    cart.status = "EXPIRED"
    cart.save(update_fields=["status", "updated_at"])

@transaction.atomic
def checkout(cart: Cart, order_creator_fn):
    """
    Convierte el carrito en una orden (delegamos creación real a `order_creator_fn`).

    Pasos:
      1) Re-chequeo de stock → valida que cada Availability siga "viva"
      2) Invoca `order_creator_fn(cart)` → debe devolver objeto Order.
      3) Cambia estado a ORDERED (no libera stock).
    """
    if cart.status != "OPEN":
        raise CartClosedError("El carrito no está abierto")

    # ── 1. RE-CHEQUEO DE STOCK ────────────────────────────────
    # ✅ OPTIMIZACIÓN: Obtener todos los product_types en una sola consulta
    lines_with_metadata = cart.items.select_for_update().select_related('product_metadata')
    
    for line in lines_with_metadata:
        reserve_fn, _ = _get_stock_funcs(line.product_metadata.product_type)
        try:
            reserve_fn(line.availability_id, line.qty)     # qty=0 ⇒ solo valida
        except InsufficientStockError:
            raise InsufficientStockError(
                f"Stock insuficiente para availability {line.availability_id}"
            )

    # ── 2. CREAR ORDEN REAL ──────────────────────────────────
    order = order_creator_fn(cart)

    # ── 3. MARCAR CARRITO ────────────────────────────────────
    cart.status = "ORDERED"
    cart.updated_at = timezone.now()
    cart.save(update_fields=["status", "updated_at"])

    # ── 4. LOGGING ────────────────────────────────────────────
    import logging
    logger = logging.getLogger(__name__)
    logger.info("cart_checked_out", extra={"cart_id": cart.id, "order_id": order.id})

    return order 