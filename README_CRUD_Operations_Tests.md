# Documentación de Tests CRUD para la App Productos

**Archivo:** `api.products.tests.test_crud_operations`

## Resumen

Este documento describe los tests automatizados para operaciones CRUD (Crear, Leer, Actualizar, Eliminar) de productos. Los tests verifican el funcionamiento correcto de los modelos de productos y sus relaciones.

---

## Estructura de Tests

### 1. **Test CRUD Básico** (`test_crud_operations.py`)
- **Propósito:** Operaciones CRUD fundamentales
- **Cobertura:** Creación, lectura, actualización, eliminación
- **Enfoque:** Funcionalidad básica de modelos

### 2. **Test de Stock y Auditoría** (`test_stock_and_audit_system.py`)
- **Propósito:** Sistema integrado de gestión de stock con auditoría
- **Cobertura:** Reservas, liberaciones, logging, métricas
- **Enfoque:** Funcionalidad avanzada de negocio

### 3. **Test de Modelos** (`test_models.py`)
- **Propósito:** Validaciones y propiedades de modelos Django
- **Cobertura:** Validaciones, propiedades calculadas, métodos
- **Enfoque:** Integridad de datos y comportamiento de modelos

---

## Tests CRUD Básicos

### Operaciones CREATE
- Creación de actividades con datos válidos
- Creación de disponibilidades de actividad
- Creación de transporte y disponibilidades
- Validaciones de campos obligatorios

### Operaciones READ
- Listado de todos los productos
- Filtros por dificultad, idioma, fecha
- Consultas con datos relacionados
- Agregaciones y estadísticas

### Operaciones UPDATE
- Actualización de campos básicos
- Actualización de stock de disponibilidades
- Actualización masiva de registros
- Validaciones durante actualización

### Operaciones DELETE
- Eliminación de actividades individuales
- Eliminación con datos relacionados
- Eliminación masiva
- Efectos en cascada

---

## Tests de Stock y Auditoría

### Servicios de Auditoría
- **Contexto de Request:** Obtención de información de usuario y sesión
- **Logging de Operaciones:** Registro de reservas, liberaciones, verificaciones
- **Logging de Cambios:** Tracking detallado de modificaciones de stock
- **Métricas de Stock:** Cálculo de utilización y estadísticas

### Servicios de Stock
- **Verificación de Stock:** Comprobación de disponibilidad
- **Reservas:** Asignación de espacios/plazas
- **Liberaciones:** Devolución de espacios reservados
- **Validación Masiva:** Verificación de múltiples productos

### Sistema Integrado
- **Operaciones con Auditoría:** Reservas con logging automático
- **Consultas de Auditoría:** Filtros y búsquedas en logs
- **Resúmenes de Stock:** Estadísticas por producto
- **Validación Masiva:** Verificación de múltiples reservas

### Manejo de Errores
- **Errores de Base de Datos:** Recuperación graciosa
- **Validaciones de Negocio:** Cantidades inválidas, stock insuficiente
- **Casos Edge:** Límites y condiciones extremas

### Rendimiento
- **Reservas Concurrentes:** Manejo de múltiples hilos
- **Rendimiento de Auditoría:** Creación masiva de logs
- **Optimización:** Tiempos de ejecución aceptables

---

## Tests de Modelos

### Validaciones de Campos
- **Campos Obligatorios:** Verificación de requerimientos
- **Rangos y Límites:** Validación de valores permitidos
- **Formatos:** Verificación de tipos de datos
- **Restricciones Únicas:** Validación de unicidad

### Propiedades Calculadas
- **Nombre Completo:** Concatenación de campos
- **Disponibilidad:** Cálculo de estado activo
- **Tipo de Producto:** Determinación automática
- **Duración:** Cálculo de días/horas

### Métodos de Clase
- **Logging:** Métodos para auditoría automática
- **Actualización:** Métodos para métricas
- **Validación:** Métodos de verificación

### Relaciones
- **Foreign Keys:** Verificación de integridad referencial
- **Jerarquías:** Relaciones padre-hijo
- **Many-to-Many:** Asociaciones complejas

---

## Configuración

### Requisitos
- Django 4.2+
- pytest
- Base de datos SQLite para tests

### Ejecución
```bash
# Ejecutar todos los tests
pytest myweb/api/products/tests/

# Ejecutar test específico
pytest myweb/api/products/tests/test_crud_operations.py
pytest myweb/api/products/tests/test_stock_and_audit_system.py
pytest myweb/api/products/tests/test_models.py

# Ejecutar con marcadores
pytest -m unit
```

---

## Cobertura de Tests

### Test CRUD Básico
- ✅ Creación de productos
- ✅ Lectura y filtrado
- ✅ Actualización de datos
- ✅ Eliminación y cascada
- ✅ Validaciones básicas
- ✅ Relaciones entre modelos
- ✅ Consultas avanzadas
- ✅ Operaciones masivas
- ✅ Rendimiento

### Test de Stock y Auditoría
- ✅ Servicios de auditoría
- ✅ Servicios de stock
- ✅ Sistema integrado
- ✅ Manejo de errores
- ✅ Casos edge
- ✅ Rendimiento
- ✅ Concurrencia
- ✅ Cobertura completa

### Test de Modelos
- ✅ Validaciones de campos
- ✅ Propiedades calculadas
- ✅ Métodos de clase
- ✅ Relaciones
- ✅ Representaciones
- ✅ Jerarquías

---

## Mantenimiento

### Agregar Nuevos Tests
1. Identificar funcionalidad a probar
2. Crear test en archivo apropiado
3. Usar marcadores pytest para categorización
4. Documentar propósito del test

### Actualizar Tests Existentes
1. Verificar compatibilidad con cambios de modelo
2. Actualizar datos de prueba si es necesario
3. Mantener cobertura de casos edge
4. Validar rendimiento

### Debugging
- Usar `pytest -v` para output detallado
- Usar `pytest --pdb` para debugging interactivo
- Revisar logs de auditoría para errores
- Verificar limpieza de datos en tearDown

---

## Referencias

- Django Documentation: Testing
- Pytest Documentation: Best Practices
- Python unittest Framework

---

## 1. Introducción

### 1.1 Propósito

Los tests CRUD aseguran que las operaciones básicas de base de datos funcionen correctamente para todos los modelos de productos del sistema turístico.

### 1.2 Apps Cubiertas

- **`api.products`** - Modelos principales de productos
- **`api.users`** - Usuarios (solo para configuración)

### 1.3 Tecnologías

- Django TestCase
- Pytest
- SQLite (base de datos de test)
- Python 3.11+

---

## 2. Estructura de los Tests

### 2.1 Organización

Los tests están en la clase `CRUDOperationsTestCase` que incluye:

- **Setup automático** de datos base
- **Limpieza automática** después de cada test
- **Aislamiento** entre tests
- **Marcado** con `@pytest.mark.unit`

### 2.2 Datos Base Creados

- Ubicación (Buenos Aires)
- Proveedor (Turismo Test S.A.)
- Categoría (Aventura)
- Usuario de prueba

---

## 3. Tests Implementados

### 📁 **Archivo: `test_crud_operations.py`**

#### 3.1 Tests de Creación (CREATE)

##### `test_create_activity_with_valid_data`
- **Qué hace:** Crea una actividad con datos válidos
- **Verifica:** Persistencia en base de datos, valores correctos
- **Campos probados:** nombre, descripción, ubicación, fecha, duración, espacios

##### `test_create_activity_with_invalid_data`
- **Qué hace:** Intenta crear actividades con datos inválidos
- **Verifica:** Validaciones de campos obligatorios y rangos
- **Casos:** duración negativa, espacios excedidos

##### `test_create_activity_availability`
- **Qué hace:** Crea disponibilidad para una actividad
- **Verifica:** Relación actividad-disponibilidad, precios, asientos

##### `test_create_transportation_and_availability`
- **Qué hace:** Crea transporte con disponibilidad
- **Verifica:** Relación transporte-disponibilidad, fechas, precios

#### 3.2 Tests de Lectura (READ)

##### `test_list_all_products`
- **Qué hace:** Lista todos los productos de la base de datos
- **Verifica:** Estructura de ProductsMetadata, tipos de producto
- **Muestra:** Estadísticas de productos por tipo

##### `test_read_activities_with_filters`
- **Qué hace:** Filtra actividades por dificultad e idioma
- **Verifica:** Conteos correctos, ordenamiento
- **Filtros:** dificultad, idioma, patrones de nombre

##### `test_read_activities_with_related_data`
- **Qué hace:** Lee actividades con datos relacionados
- **Verifica:** Relaciones con disponibilidades, optimización de consultas
- **Uso:** `prefetch_related` para optimización

##### `test_read_activities_with_aggregations`
- **Qué hace:** Calcula estadísticas de actividades
- **Verifica:** Conteos, promedios, agregaciones
- **Métricas:** cantidad por dificultad, duración promedio

#### 3.3 Tests de Actualización (UPDATE)

##### `test_update_activity_basic_fields`
- **Qué hace:** Actualiza campos básicos de actividades
- **Verifica:** Persistencia de cambios, validaciones
- **Campos:** nombre, descripción, duración

##### `test_update_activity_with_invalid_data`
- **Qué hace:** Intenta actualizar con datos inválidos
- **Verifica:** Validaciones durante actualización
- **Casos:** valores fuera de rango, campos obligatorios

##### `test_update_activity_availability_stock`
- **Qué hace:** Actualiza stock de disponibilidades
- **Verifica:** Cambios en asientos reservados, validaciones
- **Operaciones:** reservar, liberar asientos

##### `test_bulk_update_activities`
- **Qué hace:** Actualiza múltiples actividades a la vez
- **Verifica:** Eficiencia de operaciones masivas
- **Uso:** `update()` para cambios masivos

#### 3.4 Tests de Eliminación (DELETE)

##### `test_delete_activity`
- **Qué hace:** Elimina una actividad individual
- **Verifica:** Eliminación exitosa, limpieza de datos
- **Confirmación:** Verifica que no existe en base de datos

##### `test_delete_activity_with_related_data`
- **Qué hace:** Elimina actividad con datos relacionados
- **Verifica:** Eliminación en cascada, integridad referencial
- **Relaciones:** disponibilidades, metadata

##### `test_bulk_delete_activities`
- **Qué hace:** Elimina múltiples actividades
- **Verifica:** Eficiencia de eliminaciones masivas
- **Uso:** `delete()` con filtros

#### 3.5 Tests de Validación

##### `test_activity_validation_constraints`
- **Qué hace:** Verifica restricciones del modelo Activities
- **Verifica:** Campos obligatorios, rangos válidos
- **Método:** `full_clean()` para validación completa

##### `test_activity_availability_validation`
- **Qué hace:** Verifica validaciones específicas de disponibilidad
- **Verifica:** Precios, fechas, stock
- **Casos:** asientos reservados exceden total

#### 3.6 Tests de Relaciones

##### `test_activity_location_relationship`
- **Qué hace:** Verifica relación actividad-ubicación
- **Verifica:** ForeignKey, acceso bidireccional
- **Relación:** Activities → Location

##### `test_activity_availability_relationship`
- **Qué hace:** Verifica relación actividad-disponibilidad
- **Verifica:** OneToMany, eliminación en cascada
- **Relación:** Activities → ActivityAvailability

#### 3.7 Tests de Consultas Avanzadas

##### `test_advanced_queries_with_annotations`
- **Qué hace:** Prueba consultas con anotaciones
- **Verifica:** Agregaciones, cálculos estadísticos
- **Uso:** `annotate()`, `Count()`, `Avg()`

##### `test_queries_with_subqueries`
- **Qué hace:** Prueba consultas con subconsultas
- **Verifica:** Consultas complejas, optimización
- **Uso:** `Subquery()`, `OuterRef()`

#### 3.8 Tests de Rendimiento

##### `test_query_performance_with_select_related`
- **Qué hace:** Compara consultas optimizadas vs no optimizadas
- **Verifica:** Reducción de queries, mejor rendimiento
- **Uso:** `select_related()` para optimización

##### `test_bulk_operations_performance`
- **Qué hace:** Prueba operaciones masivas
- **Verifica:** Eficiencia de `bulk_create` vs creación individual
- **Métrica:** Tiempo de ejecución, cantidad de registros

---

### 📁 **Archivo: `test_stock_and_audit_system.py`**

#### 3.9 Tests de Servicios de Auditoría

##### `test_get_request_context_with_request`
- **Qué hace:** Obtiene contexto de request con datos completos
- **Verifica:** Información de usuario, sesión y request ID
- **Uso:** Mock de RequestFactory

##### `test_get_request_context_without_request`
- **Qué hace:** Obtiene contexto sin request
- **Verifica:** Valores por defecto, request ID generado
- **Casos:** Contexto mínimo

##### `test_log_stock_operation_success`
- **Qué hace:** Registra operación exitosa de stock
- **Verifica:** Logging correcto, campos obligatorios
- **Campos:** tipo operación, producto, cantidad, éxito

##### `test_log_stock_operation_failure`
- **Qué hace:** Registra operación fallida de stock
- **Verifica:** Logging de errores, mensajes de error
- **Campos:** éxito false, mensaje de error

##### `test_log_stock_change_increase`
- **Qué hace:** Registra cambio específico de stock
- **Verifica:** Tracking detallado, tipo de cambio
- **Relación:** Log de auditoría → Cambio específico

##### `test_update_stock_metrics_new`
- **Qué hace:** Crea nuevas métricas de stock
- **Verifica:** Cálculo de utilización, estadísticas
- **Métricas:** capacidad total, reservado, disponible

##### `test_update_stock_metrics_existing`
- **Qué hace:** Actualiza métricas existentes
- **Verifica:** Actualización en lugar de creación
- **Comportamiento:** Upsert de métricas

#### 3.10 Tests de Servicios de Stock

##### `test_check_activity_stock_sufficient`
- **Qué hace:** Verifica stock suficiente para actividad
- **Verifica:** Disponibilidad, cantidades correctas
- **Retorna:** Dict con información de stock

##### `test_check_activity_stock_insufficient`
- **Qué hace:** Verifica stock insuficiente
- **Verifica:** Detección de falta de stock
- **Retorna:** Dict con flag de suficiencia

##### `test_check_activity_stock_invalid_quantity`
- **Qué hace:** Verifica con cantidad inválida
- **Verifica:** Validaciones de cantidad
- **Casos:** 0, valores negativos

##### `test_reserve_activity_success`
- **Qué hace:** Reserva exitosa de actividad
- **Verifica:** Actualización de stock, retorno correcto
- **Operación:** Incremento de asientos reservados

##### `test_reserve_activity_insufficient_stock`
- **Qué hace:** Reserva con stock insuficiente
- **Verifica:** Excepción apropiada
- **Error:** InsufficientStockError

##### `test_release_activity_success`
- **Qué hace:** Liberación exitosa de actividad
- **Verifica:** Decremento de stock, retorno correcto
- **Operación:** Decremento de asientos reservados

##### `test_check_transportation_stock`
- **Qué hace:** Verifica stock de transporte
- **Verifica:** Disponibilidad de asientos
- **Producto:** TransportationAvailability

##### `test_reserve_transportation_success`
- **Qué hace:** Reserva exitosa de transporte
- **Verifica:** Actualización de stock de transporte
- **Operación:** Reserva de asientos

##### `test_check_room_stock`
- **Qué hace:** Verifica stock de habitaciones
- **Verifica:** Disponibilidad de habitaciones
- **Producto:** RoomAvailability

##### `test_reserve_room_success`
- **Qué hace:** Reserva exitosa de habitación
- **Verifica:** Actualización de stock de habitación
- **Operación:** Reserva de habitaciones

##### `test_check_flight_stock`
- **Qué hace:** Verifica stock de vuelos
- **Verifica:** Disponibilidad de asientos de vuelo
- **Producto:** Flights

##### `test_reserve_flight_success`
- **Qué hace:** Reserva exitosa de vuelo
- **Verifica:** Actualización de stock de vuelo
- **Operación:** Reserva de asientos

#### 3.11 Tests de Sistema Integrado

##### `test_stock_operation_with_audit_logging`
- **Qué hace:** Combina operación de stock con auditoría
- **Verifica:** Logging automático durante reserva
- **Integración:** Stock + Auditoría

##### `test_audit_query_service_basic`
- **Qué hace:** Consulta básica de logs de auditoría
- **Verifica:** Filtrado por tipo de producto
- **Servicio:** StockAuditQueryService

##### `test_audit_query_service_with_filters`
- **Qué hace:** Consulta con filtros avanzados
- **Verifica:** Filtros por fecha, tipo operación, éxito
- **Filtros:** Múltiples criterios

##### `test_get_stock_summary_activity`
- **Qué hace:** Obtiene resumen de stock de actividad
- **Verifica:** Estadísticas de disponibilidad
- **Resumen:** Total, reservado, disponible

##### `test_get_stock_summary_transportation`
- **Qué hace:** Obtiene resumen de stock de transporte
- **Verifica:** Estadísticas de transporte
- **Resumen:** Total, reservado, disponible

##### `test_validate_bulk_stock_reservation_success`
- **Qué hace:** Valida múltiples reservas exitosas
- **Verifica:** Validación masiva sin errores
- **Operación:** Múltiples productos

##### `test_validate_bulk_stock_reservation_with_errors`
- **Qué hace:** Valida múltiples reservas con errores
- **Verifica:** Detección de errores en validación masiva
- **Errores:** Stock insuficiente, productos inexistentes

#### 3.12 Tests de Manejo de Errores

##### `test_error_handling_in_log_stock_operation`
- **Qué hace:** Maneja errores en logging de auditoría
- **Verifica:** Recuperación graciosa de errores
- **Casos:** Errores de base de datos

##### `test_error_handling_in_stock_services`
- **Qué hace:** Maneja errores en servicios de stock
- **Verifica:** Excepciones apropiadas
- **Casos:** Producto no encontrado, cantidad inválida

#### 3.13 Tests de Rendimiento

##### `test_concurrent_reservations`
- **Qué hace:** Prueba reservas concurrentes
- **Verifica:** Manejo de concurrencia
- **Técnica:** Múltiples hilos

##### `test_audit_system_performance`
- **Qué hace:** Prueba rendimiento del sistema de auditoría
- **Verifica:** Creación masiva de logs
- **Métrica:** Tiempo de ejecución

#### 3.14 Tests de Casos Edge

##### `test_stock_validation_edge_cases`
- **Qué hace:** Prueba casos límite en validación
- **Verifica:** Stock exacto, insuficiente por 1
- **Casos:** Límites de stock

##### `test_stock_release_edge_cases`
- **Qué hace:** Prueba casos límite en liberación
- **Verifica:** Liberar más de lo reservado
- **Casos:** Liberación excesiva

##### `test_metrics_with_zero_capacity`
- **Qué hace:** Prueba métricas con capacidad cero
- **Verifica:** Manejo de división por cero
- **Caso:** Capacidad total = 0

#### 3.15 Tests de Cobertura Completa

##### `test_all_product_types_audit_support`
- **Qué hace:** Verifica soporte de auditoría para todos los tipos
- **Verifica:** Logging para activity, transportation, room, flight
- **Cobertura:** Todos los tipos de producto

##### `test_audit_system_coverage`
- **Qué hace:** Prueba cobertura completa del sistema
- **Verifica:** Diferentes escenarios de operaciones
- **Escenarios:** Reserve, release, check, success/failure

---

### 📁 **Archivo: `test_models.py`**

#### 3.16 Tests de Validaciones de Modelos

##### `test_activity_model_validation`
- **Qué hace:** Valida restricciones del modelo Activities
- **Verifica:** Campos obligatorios, rangos válidos
- **Validaciones:** Duración, espacios máximos, fechas

##### `test_activity_availability_validation`
- **Qué hace:** Valida restricciones de disponibilidad
- **Verifica:** Precios, fechas, stock
- **Validaciones:** Asientos reservados ≤ total

##### `test_transportation_model_validation`
- **Qué hace:** Valida restricciones del modelo Transportation
- **Verifica:** Capacidad, fechas, precios
- **Validaciones:** Origen ≠ destino

##### `test_room_model_validation`
- **Qué hace:** Valida restricciones del modelo Room
- **Verifica:** Capacidad, precios, fechas
- **Validaciones:** Fechas de check-in/out

##### `test_flight_model_validation`
- **Qué hace:** Valida restricciones del modelo Flights
- **Verifica:** Número de vuelo, fechas, asientos
- **Validaciones:** Duración del vuelo

#### 3.17 Tests de Propiedades Calculadas

##### `test_activity_properties`
- **Qué hace:** Prueba propiedades calculadas de Activities
- **Verifica:** Nombre completo, disponibilidad, tipo
- **Propiedades:** Métodos computados

##### `test_availability_properties`
- **Qué hace:** Prueba propiedades de disponibilidad
- **Verifica:** Asientos disponibles, estado
- **Propiedades:** Cálculos de stock

##### `test_transportation_properties`
- **Qué hace:** Prueba propiedades de transporte
- **Verifica:** Duración del viaje, estado
- **Propiedades:** Cálculos de tiempo

##### `test_room_properties`
- **Qué hace:** Prueba propiedades de habitación
- **Verifica:** Duración de estadía, precio total
- **Propiedades:** Cálculos de estadía

#### 3.18 Tests de Métodos de Clase

##### `test_activity_methods`
- **Qué hace:** Prueba métodos específicos de Activities
- **Verifica:** Métodos de logging, actualización
- **Métodos:** Funcionalidad de negocio

##### `test_availability_methods`
- **Qué hace:** Prueba métodos de disponibilidad
- **Verifica:** Métodos de stock, validación
- **Métodos:** Gestión de inventario

##### `test_transportation_methods`
- **Qué hace:** Prueba métodos de transporte
- **Verifica:** Métodos de reserva, validación
- **Métodos:** Gestión de transportes

#### 3.19 Tests de Relaciones

##### `test_activity_relationships`
- **Qué hace:** Verifica relaciones de Activities
- **Verifica:** Foreign keys, relaciones inversas
- **Relaciones:** Location, Category, Suppliers

##### `test_availability_relationships`
- **Qué hace:** Verifica relaciones de disponibilidad
- **Verifica:** Relaciones con productos principales
- **Relaciones:** Activity → ActivityAvailability

##### `test_transportation_relationships`
- **Qué hace:** Verifica relaciones de transporte
- **Verifica:** Origen, destino, proveedor
- **Relaciones:** Location, Suppliers

##### `test_room_relationships`
- **Qué hace:** Verifica relaciones de habitación
- **Verifica:** Alojamiento, disponibilidad
- **Relaciones:** Lodgment, RoomAvailability

#### 3.20 Tests de Representación

##### `test_model_string_representations`
- **Qué hace:** Prueba representaciones string de modelos
- **Verifica:** Métodos `__str__` y `__repr__`
- **Representación:** Formato legible

##### `test_model_meta_options`
- **Qué hace:** Prueba opciones Meta de modelos
- **Verifica:** Ordenamiento, índices, constraints
- **Meta:** Configuración de modelos

#### 3.21 Tests de Jerarquías

##### `test_product_hierarchy`
- **Qué hace:** Prueba jerarquía de productos
- **Verifica:** Herencia, polimorfismo
- **Jerarquía:** Productos base → Específicos

##### `test_availability_hierarchy`
- **Qué hace:** Prueba jerarquía de disponibilidad
- **Verifica:** Patrones comunes, diferencias
- **Jerarquía:** Disponibilidad base → Específica

---

## 4. Ejecución de Tests

### 4.1 Comandos Básicos

```bash
# Todos los tests CRUD
python manage.py test api.products.tests.test_crud_operations -v 2

# Test específico
python manage.py test api.products.tests.test_crud_operations.CRUDOperationsTestCase.test_list_all_products -v 2

# Tests por categoría
python manage.py test api.products.tests.test_crud_operations -k "create" -v 2
python manage.py test api.products.tests.test_crud_operations -k "read" -v 2
python manage.py test api.products.tests.test_crud_operations -k "update" -v 2
python manage.py test api.products.tests.test_crud_operations -k "delete" -v 2
```

### 4.2 Configuración

Los tests usan:
- Base de datos SQLite en memoria
- Logging configurado para suprimir mensajes
- Limpieza automática de datos

---

## 5. Cobertura de Tests

### 5.1 Resumen

- **Total de tests:** 23
- **Apps cubiertas:** 2 (products, users)
- **Modelos principales:** 12
- **Operaciones CRUD:** 100% cubiertas

### 5.2 Distribución por Tipo

| Tipo | Cantidad | Descripción |
|------|----------|-------------|
| CREATE | 4 | Creación con validaciones |
| READ | 4 | Listado, filtros, agregaciones |
| UPDATE | 4 | Actualización individual y masiva |
| DELETE | 3 | Eliminación individual y masiva |
| Validación | 2 | Restricciones y reglas |
| Relaciones | 2 | Foreign keys y cascada |
| Consultas | 2 | Anotaciones y subconsultas |
| Rendimiento | 2 | Optimización y operaciones masivas |

### 5.3 Modelos Cubiertos

- **Activities** - Actividades turísticas
- **ActivityAvailability** - Disponibilidad de actividades
- **Flights** - Vuelos
- **Lodgments** - Alojamientos
- **Transportation** - Transportes
- **TransportationAvailability** - Disponibilidad de transportes
- **ProductsMetadata** - Metadata de productos
- **Location** - Ubicaciones
- **Suppliers** - Proveedores
- **Category** - Categorías
- **Users** - Usuarios (configuración)

---

## 6. Mantenimiento

### 6.1 Criterios de Éxito

Un test es exitoso cuando:
- Pasa sin errores
- Valida funcionalidad específica
- Mantiene aislamiento
- Proporciona cobertura adecuada

### 6.2 Recomendaciones

- Ejecutar tests regularmente
- Actualizar cuando cambien modelos
- Agregar tests para nuevas funcionalidades
- Revisar métricas de rendimiento

---

