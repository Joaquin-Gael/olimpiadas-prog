from decimal import Decimal
from ninja import Router
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404, get_list_or_404
from django.db import transaction

from .models import Cart, CartItem
from .schemas import CartOut, CartItemOut, ItemAddIn, ItemQtyPatchIn, UserBasicInfo, PackageAddIn, \
    OrderCheckoutResponseSchema
from api.products.models import ProductsMetadata
from .services import services_cart as cart_srv
from .services import services_orders as order_srv
from .idempotency import store_idempotent
from api.products.services.stock_services import InsufficientStockError

from api.core.auth import SyncJWTBearer

from .services.services_cart import console

router = Router(
    tags=["Cart"],
    auth=SyncJWTBearer()
)

# ── Helper: obtener (o crear) carrito OPEN del usuario ─────────
def _get_open_cart(user, currency=None):
    """
    Obtiene o crea un carrito abierto para el usuario.
    
    Args:
        user: Instancia del modelo Users
        currency: Moneda del carrito (default: USD)
    
    Returns:
        Cart: Instancia del carrito abierto
    """
    # Validar que el usuario esté activo
    if not user.is_active:
        raise HttpError(401, "Usuario inactivo")
    
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
    - **401 Unauthorized**: Si el usuario no está autenticado, el token es inválido, o el usuario está inactivo.

    ### Ejemplo de respuesta (200):
    ```json
    {
        "id": 1,
        "user_id": 123,
        "status": "OPEN",
        "currency": "USD",
        "items_cnt": 2,
        "total": 100.00,
        "updated_at": "2024-01-15T10:30:00Z",
        "items": [
            {
                "id": 1,
                "availability_id": 100,
                "product_metadata_id": 45,
                "qty": 2,
                "unit_price": 50.0,
                "currency": "USD",
                "config": {}
            }
        ]
    }
    ```
    """
    try:
        # Validar que el usuario esté autenticado
        if not request.user:
            raise HttpError(401, "Usuario no autenticado")
        
        # Obtener o crear carrito
        cart = _get_open_cart(request.user, "USD")
        
        # Crear respuesta con información del usuario
        try:
            cart_data = CartOut.from_orm(cart)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error serializando carrito {cart.id}: {str(e)}")
            raise HttpError(500, "Error al procesar carrito")
        
        # Manejar carrito vacío
        if cart.items_cnt == 0:
            cart_data.items = []
            cart_data.total = 0.0

        
        return cart_data
        
    except HttpError:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error en get_cart: {str(e)}")
        raise HttpError(500, "Error interno del servidor")

# ───────────────────────────────────────────────────────────────
# 1.1. Obtener carrito con información completa del usuario
# ───────────────────────────────────────────────────────────────
@router.get("/cart/user-info/", response=dict)
def get_cart_with_user_info(request):
    """
    Recupera el carrito actual junto con información completa del usuario autenticado.

    ### Descripción:
    Este endpoint devuelve tanto la información del carrito como datos completos del usuario,
    útil para mostrar información personalizada en el frontend.

    ### Headers requeridos:
    - **Authorization**: Proporciona el token de autenticación JWT del usuario. Es obligatorio.

    ### Respuestas:
    - **200 OK**: Retorna un objeto JSON con información del carrito y del usuario.
    - **401 Unauthorized**: Si el usuario no está autenticado o está inactivo.

    ### Ejemplo de respuesta (200):
    ```json
    {
        "user": {
            "id": 123,
            "first_name": "Juan",
            "last_name": "Pérez",
            "email": "juan@example.com",
            "telephone": "123456789",
            "born_date": "1990-01-01",
            "state": "active"
        },
        "cart": {
            "id": 1,
            "user_id": 123,
            "status": "OPEN",
            "currency": "USD",
            "items_cnt": 2,
            "total": 100.00,
            "updated_at": "2024-01-15T10:30:00Z",
            "items": [...]
        }
    }
    ```
    """
    try:
        # Validar que el usuario esté autenticado
        if not request.user:
            raise HttpError(401, "Usuario no autenticado")
        # TODO: manejar permisos porque de esto ya se encarga en autenticador
        
        # Obtener o crear carrito
        cart = _get_open_cart(request.user, "USD")
        
        # Preparar información del usuario con validación
        user_info = {
            "id": request.user.id,
            "first_name": request.user.first_name or "",
            "last_name": request.user.last_name or "",
            "email": request.user.email or "",
            "telephone": request.user.telephone or "",
            "born_date": request.user.born_date.isoformat() if request.user.born_date else None,
            "state": request.user.state or ""
        }
        
        # Preparar información del carrito con manejo de errores
        try:
            cart_info = CartOut.from_orm(cart)
            
            # Manejar carrito vacío
            if cart.items_cnt == 0:
                cart_info.items = []
                cart_info.total = 0.0
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error serializando carrito {cart.id}: {str(e)}")
            raise HttpError(500, "Error al procesar carrito")
        
        return {
            "user": user_info,
            "cart": cart_info.dict()
        }
        
    except HttpError:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error en get_cart_with_user_info: {str(e)}")
        raise HttpError(500, "Error interno del servidor")

# ───────────────────────────────────────────────────────────────
# 2. Añadir ítem
# ───────────────────────────────────────────────────────────────
@router.post("/cart/items/", response={200: CartItemOut})
#@store_idempotent()
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
    ```
    """
    try:
        # Validar que el producto existe
        metadata = get_object_or_404(ProductsMetadata, id=payload.product_metadata_id)

        console.print(f"metadata: {metadata}")
        
        # Validar datos de entrada
        if payload.qty <= 0:
            raise HttpError(400, "La cantidad debe ser mayor a 0")
        
        if payload.unit_price <= 0:
            raise HttpError(400, "El precio unitario debe ser mayor a 0")
        
        cart = _get_open_cart(request.user, metadata.currency)

        item = cart_srv.add_item(
            cart=cart,
            metadata=metadata,
            availability_id=payload.availability_id,
            qty=payload.qty,
            unit_price=Decimal(str(payload.unit_price)),
            config=payload.config
        )

        return {
            "id": item.id,
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
    except HttpError:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error agregando item al carrito: {str(e)}")
        raise HttpError(500, "Error interno del servidor")

# ───────────────────────────────────────────────────────────────
# 2.1. Añadir paquete al carrito
# ───────────────────────────────────────────────────────────────
@router.post("/cart/packages/", response={200: list[CartItemOut]})
#@store_idempotent()
def add_package(request, payload: PackageAddIn):
    """
    Añade un paquete completo al carrito del usuario autenticado.

    ### Descripción:
    Este endpoint permite agregar paquetes completos al carrito en estado `OPEN` del usuario. 
    Un paquete puede contener múltiples componentes (actividades, vuelos, alojamientos, etc.).
    Valida la disponibilidad de todos los componentes y reserva stock antes de agregar el paquete.

    ### Headers requeridos:
    - **Authorization**: Proporciona el token de autenticación JWT del usuario. Es obligatorio.
    - **Idempotency-Key**: Clave opcional para garantizar la idempotencia de la solicitud.

    ### Parámetros en el cuerpo de la solicitud:
    - **package_id**: ID del paquete a agregar.
    - **qty**: Cantidad de paquetes a agregar.
    - **config**: Configuración opcional del paquete (ejemplo: fechas, preferencias).

    ### Respuestas:
    - **200 OK**: Retorna una lista JSON con la información de todos los componentes agregados.
    - **404 Not Found**: Si el paquete no existe o no está activo.
    - **409 Conflict**: Si el stock es insuficiente o el carrito está cerrado.
    - **422 Unprocessable Entity**: Si ocurre un conflicto de moneda diferente.
    - **401 Unauthorized**: Si el usuario no está autenticado.

    ### Ejemplo de respuesta (200):
    ```json
    [
        {
            "id": 1,
            "availability_id": 100,
            "product_metadata_id": 45,
            "qty": 2,
            "unit_price": 50.0,
            "currency": "USD",
            "config": {}
        },
        {
            "id": 2,
            "availability_id": 101,
            "product_metadata_id": 46,
            "qty": 1,
            "unit_price": 75.0,
            "currency": "USD",
            "config": {}
        }
    ]
    ```
    """
    try:
        # Validar datos de entrada
        if payload.qty <= 0:
            raise HttpError(400, "La cantidad debe ser mayor a 0")
        
        # Obtener carrito abierto
        cart = _get_open_cart(request.user, "USD")  # Moneda por defecto para paquetes
        
        # Agregar paquete al carrito usando el servicio
        created_items = cart_srv.add_package(
            cart=cart,
            package_id=payload.package_id,
            qty=payload.qty,
            config=payload.config
        )
        
        # Convertir items a formato de respuesta
        response_items = []
        for item in created_items:
            response_items.append({
                "id": item.id,
                "availability_id": item.availability_id,
                "product_metadata_id": item.product_metadata.id,
                "qty": item.qty,
                "unit_price": float(item.unit_price),
                "currency": item.currency,
                "config": item.config
            })
        
        return response_items
        
    except cart_srv.PackageNotFoundError as e:
        raise HttpError(404, str(e))
    except cart_srv.PackageComponentsError as e:
        raise HttpError(422, str(e))
    except cart_srv.InsufficientStockError:
        raise HttpError(409, "stock_insuficiente")
    except cart_srv.CurrencyMismatchError:
        raise HttpError(422, "moneda_distinta")
    except cart_srv.CartClosedError:
        raise HttpError(409, "carrito_cerrado")
    except HttpError:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error agregando paquete al carrito: {str(e)}")
        raise HttpError(500, "Error interno del servidor")

# ───────────────────────────────────────────────────────────────
# 3. Cambiar cantidad
# ───────────────────────────────────────────────────────────────
@router.patch("/cart/items/{item_id}/", response=CartItemOut)
#@store_idempotent()
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
    ```
    """
    try:
        # Validar cantidad
        if payload.qty <= 0:
            raise HttpError(400, "La cantidad debe ser mayor a 0")
        
        # Buscar item y validar que pertenece al usuario
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        # Actualizar cantidad
        item = cart_srv.update_qty(item, payload.qty)
        
        # Serializar respuesta
        return CartItemOut.from_orm(item)
        
    except cart_srv.InsufficientStockError:
        raise HttpError(409, "stock_insuficiente")
    except cart_srv.CartClosedError:
        raise HttpError(409, "carrito_cerrado")
    except HttpError:
        raise
    except Exception as e:
        console.print_exception(show_locals=True)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error actualizando cantidad del item {item_id}: {str(e)}")
        raise HttpError(500, "Error interno del servidor")

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
    items: list[CartItem] = get_list_or_404(CartItem, id=item_id, cart__user=request.user)
    try:
        for item in items:
            cart_srv.remove_item(item, item.cart)
    except cart_srv.CartClosedError:
        console.print_exception(show_locals=True)
        raise HttpError(409, "carrito_cerrado")
    return None

# ───────────────────────────────────────────────────────────────
# 5. Checkout  → crea Order
# ───────────────────────────────────────────────────────────────
@router.post(
    "/cart/checkout/",
    response={201: OrderCheckoutResponseSchema},
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
    ```
    """
    try:
        # Obtener carrito
        cart = _get_open_cart(request.user, "USD")
        
        # Validar que el carrito no esté vacío
        if cart.items_cnt == 0:
            raise HttpError(400, "El carrito está vacío")
        
        # Validar que el total sea mayor a 0
        if cart.total <= 0:
            raise HttpError(400, "El total del carrito debe ser mayor a 0")
        
        # Obtener idempotency key
        idemp_key = request.headers.get("Idempotency-Key") \
                    or request.headers.get("HTTP_IDEMPOTENCY_KEY")

        order = cart_srv.checkout(
            cart,
            lambda c: order_srv.create_order_from_cart(
                c.id, c.user_id, idempotency_key=idemp_key
            )
        )

        return 201, OrderCheckoutResponseSchema(
            order_id=order.id,
            total=float(order.total)
        )

    except cart_srv.CartClosedError:
        raise HttpError(409, "carrito_cerrado")
    except InsufficientStockError:
        raise HttpError(409, "stock_insuficiente")
    except order_srv.InvalidCartStateError:
        raise HttpError(409, "carrito_cerrado")
    except order_srv.OrderCreationError as e:
        raise HttpError(500, f"error_creacion_orden: {str(e)}")
    except HttpError:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error en checkout del carrito {cart.id}: {str(e)}")
        raise HttpError(500, "Error interno del servidor")