# Sistema de Auditoría y Logs de Stock

## 📋 Resumen

Se ha implementado un sistema completo de auditoría y logs para rastrear todas las operaciones de stock en el sistema de productos. Este sistema proporciona trazabilidad completa, análisis de rendimiento y detección de problemas.

## 🏗️ Arquitectura del Sistema

### Modelos de Auditoría

#### 1. `StockAuditLog`
- **Propósito**: Registra todas las operaciones de stock
- **Campos principales**:
  - `operation_type`: Tipo de operación (reserve, release, check, modify, create, delete)
  - `product_type`: Tipo de producto (activity, transportation, room, flight)
  - `product_id`: ID del producto específico
  - `quantity`: Cantidad involucrada
  - `previous_stock`: Stock anterior
  - `new_stock`: Stock después de la operación
  - `user_id`: Usuario que realizó la operación
  - `session_id`: ID de sesión
  - `request_id`: ID único de la solicitud
  - `success`: Si la operación fue exitosa
  - `error_message`: Mensaje de error si falló

#### 2. `StockChangeHistory`
- **Propósito**: Registra cambios específicos en campos de stock
- **Campos principales**:
  - `audit_log`: Referencia al log principal
  - `change_type`: Tipo de cambio (increase, decrease, set, reset)
  - `field_name`: Campo que cambió
  - `old_value`: Valor anterior
  - `new_value`: Nuevo valor
  - `change_amount`: Cantidad del cambio

#### 3. `StockMetrics`
- **Propósito**: Almacena métricas y estadísticas de stock
- **Campos principales**:
  - `total_capacity`: Capacidad total
  - `current_reserved`: Actualmente reservado
  - `current_available`: Actualmente disponible
  - `utilization_rate`: Porcentaje de utilización
  - `total_reservations`: Total de reservas
  - `total_releases`: Total de liberaciones
  - `failed_operations`: Operaciones fallidas

## 🔧 Servicios de Auditoría

### `StockAuditService`
Servicio principal para registrar operaciones de auditoría:

#### Métodos principales:
- `log_stock_operation()`: Registra una operación general
- `log_stock_change()`: Registra un cambio específico
- `update_stock_metrics()`: Actualiza métricas de stock
- `log_activity_stock_operation()`: Auditoría específica para actividades
- `log_transportation_stock_operation()`: Auditoría específica para transporte
- `log_room_stock_operation()`: Auditoría específica para habitaciones
- `log_flight_stock_operation()`: Auditoría específica para vuelos

### `StockAuditQueryService`
Servicio para consultar y analizar logs:

#### Métodos principales:
- `get_audit_logs()`: Obtiene logs con filtros
- `get_stock_changes()`: Obtiene cambios específicos
- `get_stock_metrics()`: Obtiene métricas
- `get_operation_summary()`: Obtiene resumen de operaciones

## 🌐 Endpoints de Auditoría

### Logs de Auditoría
- `GET /audit/logs/` - Lista logs con filtros
- `GET /audit/logs/{log_id}/` - Detalle de un log específico
- `GET /audit/logs/{log_id}/changes/` - Cambios de un log específico

### Cambios de Stock
- `GET /audit/changes/` - Lista cambios con filtros

### Métricas
- `GET /audit/metrics/` - Lista métricas con filtros

### Resúmenes
- `GET /audit/summary/` - Resumen de operaciones

### Consultas Específicas
- `GET /audit/product/{product_type}/{product_id}/history/` - Historial de un producto
- `GET /audit/user/{user_id}/operations/` - Operaciones de un usuario
- `GET /audit/failed-operations/` - Operaciones fallidas

## 📊 Integración con Servicios de Stock

### Funciones Actualizadas
Todas las funciones de stock han sido actualizadas para incluir auditoría:

#### `reserve_activity()`
```python
# Antes
def reserve_activity(avail_id: int, qty: int):

# Después
def reserve_activity(avail_id: int, qty: int, request=None):
    # ... lógica de reserva ...
    
    # Auditoría exitosa
    StockAuditService.log_activity_stock_operation(
        operation_type="reserve",
        availability_id=avail_id,
        quantity=qty,
        previous_reserved=previous_reserved,
        new_reserved=av.reserved_seats,
        request=request,
        success=True
    )
    
    # Actualizar métricas
    StockAuditService.update_stock_metrics(...)
```

#### `release_activity()`
```python
# Antes
def release_activity(avail_id: int, qty: int):

# Después
def release_activity(avail_id: int, qty: int, request=None):
    # ... lógica de liberación ...
    
    # Auditoría exitosa
    StockAuditService.log_activity_stock_operation(
        operation_type="release",
        availability_id=avail_id,
        quantity=qty,
        previous_reserved=previous_reserved,
        new_reserved=av.reserved_seats,
        request=request,
        success=True
    )
```

## 🔍 Casos de Uso

### 1. Trazabilidad de Operaciones
```python
# Obtener todas las operaciones de un producto
logs = StockAuditQueryService.get_audit_logs(
    product_type="activity",
    product_id=123
)
```

### 2. Análisis de Rendimiento
```python
# Obtener métricas de utilización
metrics = StockAuditQueryService.get_stock_metrics(
    product_type="activity",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)
```

### 3. Detección de Problemas
```python
# Obtener operaciones fallidas
failed_ops = StockAuditQueryService.get_audit_logs(
    success_only=False,
    start_date=datetime.now() - timedelta(days=7)
)
```

### 4. Auditoría de Usuario
```python
# Obtener operaciones de un usuario específico
user_ops = StockAuditQueryService.get_audit_logs(
    user_id=456,
    start_date=datetime.now() - timedelta(days=30)
)
```

## 📈 Métricas y Reportes

### Métricas Disponibles
- **Tasa de éxito**: Porcentaje de operaciones exitosas
- **Utilización**: Porcentaje de stock utilizado
- **Volumen de operaciones**: Total de reservas/liberaciones
- **Tiempo de respuesta**: Tiempo entre operaciones
- **Patrones de uso**: Horarios y días de mayor actividad

### Reportes Automáticos
- Resumen diario de operaciones
- Alertas de operaciones fallidas
- Análisis de tendencias de utilización
- Reporte de rendimiento por producto

## 🔒 Seguridad y Privacidad

### Información Sensible
- Los logs no almacenan datos personales sensibles
- Solo se registran IDs de usuario y sesión
- Los metadatos se almacenan de forma segura

### Retención de Datos
- Los logs se mantienen por 2 años por defecto
- Las métricas se mantienen por 5 años
- Política de limpieza automática configurable

## 🚀 Beneficios del Sistema

### Para Administradores
- **Trazabilidad completa**: Saber quién hizo qué y cuándo
- **Detección de problemas**: Identificar operaciones fallidas rápidamente
- **Análisis de rendimiento**: Métricas detalladas de utilización
- **Auditoría de seguridad**: Rastrear accesos y cambios

### Para Desarrolladores
- **Debugging mejorado**: Logs detallados para resolver problemas
- **Monitoreo en tiempo real**: Estado actual del stock
- **Análisis de patrones**: Comportamiento de usuarios y sistema

### Para Negocio
- **Optimización de stock**: Datos para mejorar la gestión
- **Prevención de pérdidas**: Detectar anomalías rápidamente
- **Cumplimiento**: Registros para auditorías externas

## 🔧 Configuración

### Variables de Entorno
```bash
# Nivel de logging de auditoría
AUDIT_LOG_LEVEL=INFO

# Retención de logs (días)
AUDIT_LOG_RETENTION_DAYS=730

# Retención de métricas (días)
AUDIT_METRICS_RETENTION_DAYS=1825
```

### Configuración de Base de Datos
```python
# Índices recomendados
class StockAuditLog(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['operation_type', 'created_at']),
            models.Index(fields=['product_type', 'product_id']),
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['success']),
        ]
```

## 📝 Próximos Pasos

### Mejoras Planificadas
1. **Alertas automáticas**: Notificaciones por email/SMS
2. **Dashboard web**: Interfaz gráfica para métricas
3. **Exportación de datos**: Reportes en Excel/PDF
4. **Machine Learning**: Predicción de demanda
5. **Integración con BI**: Conexión con herramientas de business intelligence

### Optimizaciones
1. **Particionamiento**: Dividir tablas por fecha
2. **Archivado**: Mover datos antiguos a almacenamiento frío
3. **Compresión**: Reducir tamaño de almacenamiento
4. **Caché**: Acelerar consultas frecuentes 