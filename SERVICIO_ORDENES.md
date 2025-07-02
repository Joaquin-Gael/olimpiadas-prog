# Servicio de Órdenes - Documentación

## Descripción General

El servicio `create_order_from_cart` es la pieza central que convierte un carrito temporal en una orden formal del sistema. Este servicio maneja toda la lógica de negocio necesaria para esta conversión de manera transaccional y segura.

## Ubicación

```
myweb/api/store/services/services_orders.py
```

## Funcionalidad Principal

### `create_order_from_cart(cart: Cart) -> Orders`

Convierte un carrito en estado `OPEN` en una orden formal con sus líneas de detalle.

#### Pasos del Proceso

1. **Validación del Carrito**
   - Verifica que el carrito esté en estado `OPEN`
   - Confirma que tenga al menos un ítem

2. **Re-chequeo de Stock**
   - Valida que todos los productos sigan disponibles
   - Usa `reserve_fn(availability_id, 0)` para validación sin reservar

3. **Creación del Encabezado**
   - Crea el objeto `Orders` con datos del cliente
   - Estado inicial: `"Pending"`
   - Usa la primera dirección del cliente

4. **Creación de Líneas de Detalle**
   - Convierte cada `CartItem` en `OrderDetails`
   - Usa `bulk_create` para eficiencia
   - Calcula subtotales automáticamente

#### Manejo de Errores

| Error | Causa | Respuesta |
|-------|-------|-----------|
| `InvalidCartStateError` | Carrito no en estado OPEN | 409 Conflict |
| `OrderCreationError` | Fallo en creación de orden | 500 Internal Server Error |
| `InsufficientStockError` | Stock insuficiente | 409 Conflict |

## Uso en el Endpoint

```python
# En views_cart.py
@router.post("/cart/checkout/", response={201: dict})
@store_idempotent()
@transaction.atomic
def checkout(request):
    cart = _get_open_cart(request.user, "USD")
    
    try:
        # Crear orden desde carrito
        order = order_srv.create_order_from_cart(cart)
        
        # Marcar carrito como ORDERED
        cart_srv.checkout(cart, lambda cart_obj: order)
        
    except order_srv.InvalidCartStateError:
        raise HttpError(409, "carrito_cerrado")
    except order_srv.OrderCreationError as e:
        raise HttpError(500, f"error_creacion_orden: {str(e)}")
    except InsufficientStockError:
        raise HttpError(409, "stock_insuficiente")

    return 201, {"order_id": order.id, "total": float(order.total)}
```

## Flujo Completo

```
1. Cliente añade ítems → Cart (OPEN)
2. Cliente hace checkout → POST /cart/checkout/
3. create_order_from_cart() → Orders + OrderDetails
4. cart_srv.checkout() → Cart (ORDERED)
5. Respuesta: {order_id, total}
```

## Pruebas

Las pruebas están en `myweb/api/store/tests/test_services_orders.py`:

- ✅ Creación exitosa de orden
- ✅ Validación de estado del carrito
- ✅ Validación de carrito vacío
- ✅ Múltiples ítems en carrito

### Ejecutar Pruebas

```bash
cd myweb
python manage.py test api.store.tests.test_services_orders
```

## Beneficios de esta Implementación

1. **Transaccionalidad**: Todo o nada - si falla un paso, se revierte todo
2. **Separación de Responsabilidades**: Lógica de órdenes separada de carrito
3. **Reutilización**: El servicio puede usarse desde otros lugares
4. **Testabilidad**: Fácil de probar de forma aislada
5. **Mantenibilidad**: Código organizado y documentado

## Próximos Pasos

1. **Estados de Orden**: Implementar transiciones de estado (Pending → Confirmed → Completed)
2. **Pagos**: Integrar con sistema de pagos
3. **Cancelaciones**: Liberar stock cuando se cancela orden
4. **Notificaciones**: Enviar emails de confirmación
5. **Logística**: Integrar con sistema de envíos 