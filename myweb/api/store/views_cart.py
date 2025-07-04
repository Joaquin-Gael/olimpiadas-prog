from decimal import Decimal
from ninja import Router
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone # Dependencia sin utilizar

from .models import Cart, CartItem
from .schemas import CartOut, CartItemOut, ItemAddIn, ItemQtyPatchIn
from api.products.models import ProductsMetadata
from .services import services_cart as cart_srv
from .services import services_orders as order_srv
from .idempotency import store_idempotent
from api.products.services.stock_services import InsufficientStockError

from api.core.auth import SyncJWTBearer

router = Router(
    tags=["Cart"],
    auth=SyncJWTBearer()
)

# ── Helper: obtener (o crear) carrito OPEN del usuario ─────────
def _get_open_cart(user, currency=None):
    cart = Cart.objects.filter(user=user, status="OPEN").first()
    if cart:
        return cart
    return Cart.objects.create(user=user, status="OPEN", currency=currency or "USD")

# ───────────────────────────────────────────────────────────────
# 1. Obtener carrito
# ───────────────────────────────────────────────────────────────
@router.get("/cart/", response=CartOut)
def get_cart(request):
    cart = _get_open_cart(request.user, "USD")
    return CartOut.from_orm(cart)

# ───────────────────────────────────────────────────────────────
# 2. Añadir ítem
# ───────────────────────────────────────────────────────────────
@router.post("/cart/items/", response={200: CartItemOut})
@store_idempotent()
def add_item(request, payload: ItemAddIn):
    metadata = get_object_or_404(ProductsMetadata, id=payload.product_metadata_id)
    cart = _get_open_cart(request.user, metadata.currency)

    try:
        item = cart_srv.add_item(
            cart,
            metadata,
            payload.availability_id,
            payload.qty,
            Decimal(str(payload.unit_price)),
            payload.config
        )

        return 200, {
                "id": item.cart.id,
                "availability_id": item.availability_id,
                "product_metadata_id": item.product_metadata_id,
                "qty": item.qty,
                "unit_price": float(item.unit_price),
                "currency": item.currency,
                "config": item.config
            }
    except cart_srv.InsufficientStockError:
        raise HttpError(409, "stock_insuficiente")
    except cart_srv.CurrencyMismatchError:
        raise HttpError(422, "moneda_distinta")
    except cart_srv.CartClosedError:     # improbable aquí
        raise HttpError(409, "carrito_cerrado")

# ───────────────────────────────────────────────────────────────
# 3. Cambiar cantidad
# ───────────────────────────────────────────────────────────────
@router.patch("/cart/items/{item_id}/", response=CartItemOut)
@store_idempotent()
def patch_item_qty(request, item_id: int, payload: ItemQtyPatchIn):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    try:
        item = cart_srv.update_qty(item, payload.qty)
    except cart_srv.InsufficientStockError:
        raise HttpError(409, "stock_insuficiente")
    except cart_srv.CartClosedError:
        raise HttpError(409, "carrito_cerrado")

    return CartItemOut.from_orm(item)

# ───────────────────────────────────────────────────────────────
# 4. Eliminar ítem
# ───────────────────────────────────────────────────────────────
@router.delete("/cart/items/{item_id}/", response={204: None})
def delete_item(request, item_id: int):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    try:
        cart_srv.remove_item(item)
    except cart_srv.CartClosedError:
        raise HttpError(409, "carrito_cerrado")
    return 204, None

# ───────────────────────────────────────────────────────────────
# 5. Checkout  → crea Order
# ───────────────────────────────────────────────────────────────
@router.post(
    "/cart/checkout/",
    response={201: dict},
    summary="Checkout del carrito",
    description="Convierte el carrito actual en una orden. Es idempotente y revalida stock. Requiere header Idempotency-Key."
)
@store_idempotent()
@transaction.atomic
def checkout(request):
    cart = _get_open_cart(request.user, "USD")
    idemp_key = request.headers.get("Idempotency-Key") \
                or request.headers.get("HTTP_IDEMPOTENCY_KEY")

    try:
        # Usar el servicio de carrito para hacer checkout (incluye re-chequeo de stock)
        order = cart_srv.checkout(
            cart,
            lambda c: order_srv.create_order_from_cart(
                c.id, c.user_id, idempotency_key=idemp_key
            )
        )

        return 201, {"order_id": order.id, "total": float(order.total)}

    except cart_srv.CartClosedError:
        raise HttpError(409, "carrito_cerrado")
    except InsufficientStockError:
        raise HttpError(409, "stock_insuficiente")
    except order_srv.InvalidCartStateError:
        raise HttpError(409, "carrito_cerrado")
    except order_srv.OrderCreationError as e:
        raise HttpError(500, f"error_creacion_orden: {str(e)}")