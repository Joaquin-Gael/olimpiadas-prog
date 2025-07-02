# Endpoints de Disponibilidad - Documentación

## Descripción General

Este documento describe los endpoints para gestionar la disponibilidad de vuelos y habitaciones después de su creación inicial. Estos endpoints permiten a los proveedores actualizar la disponibilidad de sus productos de manera dinámica.

---

## 1. Disponibilidad de Vuelos

Los vuelos manejan su disponibilidad directamente a través del campo `available_seats` en el modelo `Flights`.

### 1.1 Actualizar Disponibilidad de Vuelo

**Endpoint:** `PATCH /api/products/{id}/flight-availability/`

**Descripción:** Actualiza el número de asientos disponibles para un vuelo específico.

**Parámetros:**
- `id` (int, path): ID del producto (metadata)
- `available_seats` (int, query): Nuevo número de asientos disponibles

**Validaciones:**
- El producto debe ser de tipo "flight"
- El vuelo debe estar activo
- Los asientos disponibles no pueden ser negativos
- Los asientos disponibles no pueden exceder 500

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "unit_price": 150.00,
  "product_type": "flight",
  "product": {
    "id": 1,
    "airline": "American Airlines",
    "flight_number": "AA123",
    "origin": {...},
    "destination": {...},
    "departure_date": "2024-01-15",
    "departure_time": "10:30:00",
    "arrival_date": "2024-01-15",
    "arrival_time": "12:30:00",
    "duration_hours": 2,
    "class_flight": "Economy",
    "available_seats": 45,
    "luggage_info": "1 carry-on + 1 checked bag",
    "aircraft_type": "Boeing 737",
    "terminal": "A",
    "gate": "A15",
    "notes": null
  }
}
```

**Errores Posibles:**
- `400`: El producto no es un vuelo o el vuelo está inactivo
- `422`: Validaciones de negocio fallidas

### 1.2 Obtener Disponibilidad de Vuelo

**Endpoint:** `GET /api/products/{id}/flight-availability/`

**Descripción:** Obtiene la información de disponibilidad actual de un vuelo.

**Parámetros:**
- `id` (int, path): ID del producto (metadata)

**Respuesta Exitosa (200):**
```json
{
  "flight_id": 1,
  "airline": "American Airlines",
  "flight_number": "AA123",
  "available_seats": 45,
  "departure_date": "2024-01-15",
  "arrival_date": "2024-01-15",
  "is_active": true
}
```

---

## 2. Disponibilidad de Habitaciones

Las habitaciones manejan su disponibilidad a través del modelo `RoomAvailability` que permite configuraciones más complejas.

### 2.1 Crear Disponibilidad de Habitación

**Endpoint:** `POST /api/products/room-availability/`

**Descripción:** Crea una nueva disponibilidad para una habitación específica.

**Body:**
```json
{
  "room_id": 1,
  "start_date": "2024-01-15",
  "end_date": "2024-01-20",
  "available_quantity": 2,
  "price_override": 120.00,
  "currency": "USD",
  "is_blocked": false,
  "minimum_stay": 2
}
```

**Validaciones:**
- La habitación debe existir y estar activa
- El alojamiento debe estar activo
- No debe haber solapamiento de fechas con disponibilidades existentes
- Las fechas no pueden estar en el pasado
- La fecha de fin debe ser posterior a la fecha de inicio

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "room_id": 1,
  "start_date": "2024-01-15",
  "end_date": "2024-01-20",
  "available_quantity": 2,
  "price_override": 120.00,
  "currency": "USD",
  "is_blocked": false,
  "minimum_stay": 2,
  "created_at": "2024-01-10T10:30:00Z",
  "updated_at": "2024-01-10T10:30:00Z"
}
```

### 2.2 Obtener Disponibilidad Específica

**Endpoint:** `GET /api/products/room-availability/{id}/`

**Descripción:** Obtiene una disponibilidad específica de habitación.

**Parámetros:**
- `id` (int, path): ID de la disponibilidad

**Respuesta:** Igual que la creación

### 2.3 Listar Disponibilidades de una Habitación

**Endpoint:** `GET /api/products/room/{room_id}/availabilities/`

**Descripción:** Lista todas las disponibilidades de una habitación específica.

**Parámetros:**
- `room_id` (int, path): ID de la habitación

**Respuesta Exitosa (200):**
```json
[
  {
    "id": 1,
    "room_id": 1,
    "start_date": "2024-01-15",
    "end_date": "2024-01-20",
    "available_quantity": 2,
    "price_override": 120.00,
    "currency": "USD",
    "is_blocked": false,
    "minimum_stay": 2,
    "created_at": "2024-01-10T10:30:00Z",
    "updated_at": "2024-01-10T10:30:00Z"
  },
  {
    "id": 2,
    "room_id": 1,
    "start_date": "2024-01-25",
    "end_date": "2024-01-30",
    "available_quantity": 1,
    "price_override": null,
    "currency": "USD",
    "is_blocked": false,
    "minimum_stay": 1,
    "created_at": "2024-01-10T11:00:00Z",
    "updated_at": "2024-01-10T11:00:00Z"
  }
]
```

### 2.4 Actualizar Disponibilidad de Habitación

**Endpoint:** `PATCH /api/products/room-availability/{id}/`

**Descripción:** Actualiza una disponibilidad existente de habitación.

**Parámetros:**
- `id` (int, path): ID de la disponibilidad

**Body (campos opcionales):**
```json
{
  "start_date": "2024-01-16",
  "end_date": "2024-01-21",
  "available_quantity": 3,
  "price_override": 130.00,
  "currency": "USD",
  "is_blocked": false,
  "minimum_stay": 3
}
```

**Validaciones:**
- Las mismas que en la creación
- No debe haber solapamiento con otras disponibilidades (excluyendo la actual)

**Respuesta:** Igual que la creación

### 2.5 Eliminar Disponibilidad de Habitación

**Endpoint:** `DELETE /api/products/room-availability/{id}/`

**Descripción:** Elimina una disponibilidad de habitación.

**Parámetros:**
- `id` (int, path): ID de la disponibilidad

**Respuesta Exitosa (204):** Sin contenido

### 2.6 Listar Disponibilidades de un Alojamiento

**Endpoint:** `GET /api/products/lodgment/{lodgment_id}/rooms/availabilities/`

**Descripción:** Lista todas las disponibilidades de habitaciones de un alojamiento.

**Parámetros:**
- `lodgment_id` (int, path): ID del alojamiento
- `start_date` (date, query, opcional): Fecha de inicio para filtrar
- `end_date` (date, query, opcional): Fecha de fin para filtrar

**Respuesta Exitosa (200):**
```json
[
  {
    "room_id": 1,
    "room_type": "double",
    "name": "Habitación 101",
    "capacity": 2,
    "base_price_per_night": 100.00,
    "currency": "USD",
    "availabilities": [
      {
        "id": 1,
        "start_date": "2024-01-15",
        "end_date": "2024-01-20",
        "available_quantity": 2,
        "price_override": 120.00,
        "is_blocked": false,
        "minimum_stay": 2,
        "effective_price": 120.00
      }
    ]
  }
]
```

---

## 3. Casos de Uso Comunes

### 3.1 Actualizar Disponibilidad de Vuelo

```bash
# Reducir asientos disponibles después de una reserva
curl -X PATCH "http://localhost:8000/api/products/1/flight-availability/?available_seats=45" \
  -H "Content-Type: application/json"
```

### 3.2 Crear Disponibilidad de Habitación

```bash
# Crear disponibilidad para una habitación
curl -X POST "http://localhost:8000/api/products/room-availability/" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 1,
    "start_date": "2024-01-15",
    "end_date": "2024-01-20",
    "available_quantity": 2,
    "price_override": 120.00,
    "currency": "USD",
    "is_blocked": false,
    "minimum_stay": 2
  }'
```

### 3.3 Bloquear Habitación

```bash
# Bloquear una habitación para mantenimiento
curl -X PATCH "http://localhost:8000/api/products/room-availability/1/" \
  -H "Content-Type: application/json" \
  -d '{
    "is_blocked": true
  }'
```

### 3.4 Consultar Disponibilidad de Alojamiento

```bash
# Ver todas las disponibilidades de un alojamiento
curl -X GET "http://localhost:8000/api/products/lodgment/1/rooms/availabilities/?start_date=2024-01-15&end_date=2024-01-20"
```

---

## 4. Consideraciones de Implementación

### 4.1 Validaciones de Negocio

- **Fechas:** No se permiten fechas en el pasado
- **Solapamiento:** No se permiten rangos de fechas que se solapen
- **Cantidades:** Las cantidades disponibles no pueden ser negativas
- **Precios:** Los precios override deben ser positivos

### 4.2 Transacciones

Todos los endpoints de modificación utilizan transacciones atómicas para garantizar la consistencia de los datos.

### 4.3 Seguridad

- Verificación de que los productos estén activos
- Validación de permisos (a implementar cuando se tenga el sistema de autenticación)
- Protección contra modificaciones concurrentes

### 4.4 Rendimiento

- Uso de índices en la base de datos para consultas de fechas
- Paginación para listados grandes
- Filtros opcionales para reducir el volumen de datos

---

## 5. Próximas Mejoras

1. **Sistema de Reservas:** Integración con el sistema de reservas para validar disponibilidad en tiempo real
2. **Notificaciones:** Alertas cuando la disponibilidad sea baja
3. **Historial:** Tracking de cambios en la disponibilidad
4. **Bulk Operations:** Operaciones masivas para múltiples productos
5. **Cache:** Implementación de cache para consultas frecuentes 