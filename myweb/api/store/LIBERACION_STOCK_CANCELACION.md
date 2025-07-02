# Liberación Automática de Stock en Cancelación de Órdenes

## Descripción

Este módulo implementa la funcionalidad para liberar automáticamente el stock reservado cuando una orden cambia a estado **CANCELLED** o **REFUNDED**.

## Funcionalidad

### Comportamiento Automático

Cuando el estado de una orden (`Orders.state`) cambia a:
- `"Cancelled"` - Se libera automáticamente todo el stock reservado
- `"Refunded"` - Se libera automáticamente todo el stock reservado

### Tipos de Productos Soportados

El sistema libera stock para los siguientes tipos de productos:

| Tipo de Producto | Función de Liberación | Modelo de Disponibilidad |
|------------------|----------------------|--------------------------|
| `activity` | `release_activity()` | `ActivityAvailability` |
| `transportation` | `release_transportation()` | `TransportationAvailability` |
| `lodgment` | `release_room_availability()` | `RoomAvailability` |
| `flight` | `release_flight()` | `Flights` |

## Implementación Técnica

### 1. Campo `availability_id` en OrderDetails

Se agregó el campo `availability_id` al modelo `OrderDetails` para almacenar el ID de la disponibilidad específica:

```python
class OrderDetails(models.Model):
    # ... otros campos ...
    availability_id = models.PositiveIntegerField(
        help_text="ID de la disponibilidad específica (ActivityAvailability, RoomAvailability, etc.)"
    )
```

### 2. Señal `pre_save` en Orders

Se implementó una señal que se ejecuta antes de guardar una orden:

```python
@receiver(pre_save, sender=Orders)
def orders_release_stock_on_cancel(sender, instance: Orders, **kwargs):
    """
    Si el estado de la orden cambió a CANCELLED liberamos stock.
    """
    # Lógica de liberación automática
```

### 3. Mapeo de Funciones de Liberación

```python
_RELEASE_MAP = {
    "activity":       release_activity,
    "transportation": release_transportation,
    "lodgment":       release_room_availability,
    "flight":         release_flight,
}
```

## Características de Seguridad

### Transacciones Atómicas
- Todas las operaciones de liberación se ejecutan dentro de transacciones atómicas
- Si falla la liberación de un producto, se revierte toda la operación

### Idempotencia
- Si una orden ya está cancelada, no se libera stock duplicado
- Se compara el estado anterior con el nuevo antes de liberar

### Manejo de Errores
- Si un producto no está soportado, se ignora silenciosamente
- Si el stock ya fue liberado, se ignora el error `InsufficientStockError`

## Casos de Uso

### 1. Cancelación de Orden
```python
# Cambiar estado a CANCELLED
order.state = "Cancelled"
order.save()  # Se libera automáticamente el stock
```

### 2. Reembolso de Orden
```python
# Cambiar estado a REFUNDED
order.state = "Refunded"
order.save()  # Se libera automáticamente el stock
```

### 3. Múltiples Detalles
Si una orden tiene múltiples productos, se libera el stock de todos:
- Actividad: 3 asientos
- Habitación: 2 noches
- Transporte: 1 asiento

Al cancelar, se liberan automáticamente todos los cupos.

## Testing

Los tests cubren los siguientes escenarios:

1. **Liberación en Cancelación**: Verifica que el stock se libera al cambiar a `CANCELLED`
2. **Liberación en Reembolso**: Verifica que el stock se libera al cambiar a `REFUNDED`
3. **No Duplicación**: Verifica que no se libera stock duplicado
4. **Múltiples Detalles**: Verifica la liberación de múltiples productos
5. **Productos No Soportados**: Verifica que se ignoran sin error

## Archivos Modificados

- `models.py`: Agregado campo `availability_id` a `OrderDetails`
- `services/services_orders.py`: Modificado para incluir `availability_id` en la creación
- `signals.py`: Nuevo archivo con la señal de liberación automática
- `apps.py`: Registro de señales
- `tests/test_order_cancellation_stock_release.py`: Tests de la funcionalidad

## Migración Requerida

Para aplicar los cambios del modelo, ejecutar:

```bash
python manage.py makemigrations store
python manage.py migrate
```

## Beneficios

1. **Automatización**: No requiere intervención manual para liberar stock
2. **Consistencia**: Garantiza que el stock se libere siempre que se cancele una orden
3. **Prevención de Pérdidas**: Evita "stock fantasma" que no está disponible pero tampoco reservado
4. **Auditoría**: Mantiene trazabilidad completa del ciclo de vida del stock 