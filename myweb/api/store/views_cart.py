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

from api.products.services.helpers import serialize_product_metadata

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
    """
    Recupera el carrito actual con estado `OPEN` del usuario autenticado.

    ### Descripción:
    Este endpoint devuelve la información del carrito en estado `OPEN` asociado al usuario. Si no existe un carrito abierto, se crea uno automáticamente con la moneda predeterminada (USD).

    ### Headers requeridos:
    - **Authorization**: Proporciona el token de autenticación JWT del usuario. Es obligatorio.
      Ejemplo: `Authorization: Bearer <token_jwt>`

    ### Respuestas:
    - **200 OK**: Retorna un objeto JSON con la estructura del carrito.
    - **401 Unauthorized**: Si el usuario no está autenticado o el token es inválido.

    ### Ejemplo de respuesta (200):
    ```json
    {
        "id": 1,
        "user_id": 123,
        "status": "OPEN",
        "currency": "USD",
        "items": [
            {
                "id": 1,
                "product_metadata_id": 45,
                "qty": 2,
                "unit_price": 50.0,
                "currency": "USD",
                "config": {}
            }
        ]
    }
    """
    cart = _get_open_cart(request.user, "USD")
    return CartOut.from_orm(cart)

# ───────────────────────────────────────────────────────────────
# 2. Añadir ítem
# ───────────────────────────────────────────────────────────────
@router.post("/cart/items/", response={200: CartItemOut})
@store_idempotent()
def add_item(request, payload: ItemAddIn):
    """
    Añade un ítem al carrito del usuario autenticado.

    ### Descripción:
    Este endpoint permite agregar productos al carrito en estado `OPEN` del usuario. Valida la disponibilidad del producto y revalida el stock antes de agregar el ítem.

    ### Headers requeridos:
    - **Authorization**: Proporciona el token de autenticación JWT del usuario. Es obligatorio.
    - **Idempotency-Key**: Clave opcional para garantizar la idempotencia de la solicitud.

    ### Parámetros en el cuerpo de la solicitud:
    - **product_metadata_id**: ID de la metadata del producto.
    - **availability_id**: ID que representa la disponibilidad específica del producto.
    - **qty**: Cantidad del producto a agregar.
    - **unit_price**: Precio unitario (como decimal).
    - **config**: Configuración opcional del producto (ejemplo: selecciones personalizables).

    ### Respuestas:
    - **200 OK**: Retorna un JSON con la información del ítem agregado.
    - **409 Conflict**: Si el stock es insuficiente o el carrito está cerrado.
    - **422 Unprocessable Entity**: Si ocurre un conflicto de moneda diferente.
    - **401 Unauthorized**: Si el usuario no está autenticado.

    ### Ejemplo de respuesta (200):
    ```json
    {
        "id": 1,
        "availability_id": 100,
        "product_metadata_id": 45,
        "qty": 2,
        "unit_price": 50.0,
        "currency": "USD",
        "config": {}
    }
    """
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
            "product_metadata_id": item.product_metadata.id,
            "qty": item.qty,
            "unit_price": float(item.unit_price),
            "currency": item.currency,
            "config": item.config
        }
    except cart_srv.InsufficientStockError:
        raise HttpError(409, "stock_insuficiente")
    except cart_srv.CurrencyMismatchError:
        raise HttpError(422, "moneda_distinta")
    except cart_srv.CartClosedError:
        raise HttpError(409, "carrito_cerrado")

# ───────────────────────────────────────────────────────────────
# 3. Cambiar cantidad
# ───────────────────────────────────────────────────────────────
@router.patch("/cart/items/{item_id}/", response=CartItemOut)
@store_idempotent()
def patch_item_qty(request, item_id: int, payload: ItemQtyPatchIn):
    """
    Modifica la cantidad de un producto en el carrito.

    ### Descripción:
    Este endpoint permite actualizar la cantidad de un ítem ya existente en el carrito, siempre y cuando el carrito permanezca abierto.

    ### Headers requeridos:
    - **Authorization**: Proporciona el token de autenticación JWT del usuario. Es obligatorio.
    - **Idempotency-Key**: Clave opcional para garantizar idempotencia.

    ### Parámetros de URL:
    - **item_id**: ID del ítem dentro del carrito.

    ### Parámetros en el cuerpo de la solicitud:
    - **qty**: Nueva cantidad deseada.

    ### Respuestas:
    - **200 OK**: Retorna el ítem actualizado.
    - **409 Conflict**: Si no hay suficiente stock o el carrito está cerrado.
    - **401 Unauthorized**: Si el usuario no está autenticado.

    ### Ejemplo de respuesta (200):
    ```json
    {
        "id": 1,
        "availability_id": 100,
        "product_metadata_id": 45,
        "qty": 3,
        "unit_price": 50.0,
        "currency": "USD",
        "config": {}
    }
    """
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
    """
    Elimina un ítem del carrito.

    ### Descripción:
    Este endpoint elimina un producto específico del carrito asociado al usuario autenticado.

    ### Headers requeridos:
    - **Authorization**: Proporciona el token de autenticación JWT del usuario. Es obligatorio.

    ### Parámetros de URL:
    - **item_id**: ID del ítem a eliminar.

    ### Respuestas:
    - **204 No Content**: El ítem fue eliminado exitosamente.
    - **409 Conflict**: Si el carrito ya está cerrado.
    - **401 Unauthorized**: Si el usuario no está autenticado.
    """
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
    """
    Convierte el carrito actual en una orden.

    ### Descripción:
    Este endpoint realiza el proceso de checkout del carrito `OPEN` asociado al usuario autenticado. Valida stock, garantiza idempotencia y crea una orden.

    ### Headers requeridos:
    - **Authorization**: Proporciona el token de autenticación JWT del usuario. Es obligatorio.
    - **Idempotency-Key**: Clave opcional que asegura una operación idempotente.

    ### Respuestas:
    - **201 Created**: Orden creada exitosamente.
    - **409 Conflict**: El carrito está cerrado o no hay suficiente stock.
    - **500 Internal Server Error**: Error durante el proceso de creación de la orden.

    ### Ejemplo de respuesta (201):
    ```json
    {
        "order_id": 12345,
        "total": 150.75
    }
    """
    cart = _get_open_cart(request.user, "USD")
    idemp_key = request.headers.get("Idempotency-Key") \
                or request.headers.get("HTTP_IDEMPOTENCY_KEY")

    try:
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