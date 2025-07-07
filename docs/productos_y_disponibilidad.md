# 📋 Documentación Completa: Productos y Sistema de Disponibilidad

## 📖 Índice
1. [Introducción](#introducción)
2. [Arquitectura de Productos](#arquitectura-de-productos)
3. [Tipos de Productos](#tipos-de-productos)
4. [Sistema de Disponibilidad](#sistema-de-disponibilidad)
5. [Flujo de Reservas](#flujo-de-reservas)
6. [API Reference](#api-reference)
7. [Ejemplos Prácticos](#ejemplos-prácticos)
8. [Casos de Uso](#casos-de-uso)

---

## 🎯 Introducción

Este sistema maneja productos turísticos con un modelo de disponibilidad granular que permite control preciso de inventario por fecha, horario y variantes específicas.

### Conceptos Clave
- **Producto**: Entidad base (actividad, vuelo, alojamiento, transporte)
- **Metadata**: Información comercial (precio, proveedor, estado)
- **Disponibilidad**: Instancia específica con fecha, horario y stock
- **Reserva**: Bloqueo temporal de cupos en una disponibilidad

---

## 🏗️ Arquitectura de Productos

### Modelo General
```
ProductsMetadata (Información comercial)
    ↓
Producto Específico (Activities, Flights, Lodgments, Transportation)
    ↓
Disponibilidades (ActivityAvailability, RoomAvailability, etc.)
```

### Relaciones
```python
# Ejemplo de relación
ProductsMetadata (id=45, unit_price=50, currency="USD")
    ↓
Activities (id=100, name="Tour Machu Picchu")
    ↓
ActivityAvailability (id=1, event_date="2024-01-15", start_time="09:00", price=50, total_seats=20)
```

---

## 🎪 Tipos de Productos

### 1. 🏃 Actividades (Activities)
**Descripción**: Tours, excursiones, experiencias turísticas

**Características**:
- Fecha y horario específicos
- Cupos limitados por sesión
- Guía incluida o no
- Nivel de dificultad
- Idioma del tour

**Modelo**:
```python
class Activities(models.Model):
    name: str                    # "Tour Machu Picchu"
    description: str             # Descripción detallada
    location: Location           # Ubicación
    date: date                   # Fecha base
    start_time: time             # Horario base
    duration_hours: int          # Duración
    include_guide: bool          # Incluye guía
    maximum_spaces: int          # Cupos máximos
    difficulty_level: str        # "Easy", "Medium", "Hard"
    language: str                # "Español", "Inglés"
    available_slots: int         # Cupos disponibles
```

**Disponibilidad**:
```python
class ActivityAvailability(models.Model):
    activity: Activities         # Actividad padre
    event_date: date             # Fecha específica
    start_time: time             # Horario específico
    total_seats: int             # Total de asientos
    reserved_seats: int          # Asientos reservados
    price: Decimal               # Precio para esta fecha
    currency: str                # Moneda
    state: str                   # "active", "cancelled"
```

### 2. ✈️ Vuelos (Flights)
**Descripción**: Servicios de transporte aéreo

**Características**:
- Origen y destino
- Fecha y horario de salida/llegada
- Aerolínea y número de vuelo
- Clase de servicio
- Capacidad de asientos

**Modelo**:
```python
class Flights(models.Model):
    airline: str                 # "LATAM", "Avianca"
    flight_number: str           # "LA1234"
    origin: Location             # Aeropuerto origen
    destination: Location        # Aeropuerto destino
    departure_date: date         # Fecha de salida
    arrival_date: date           # Fecha de llegada
    departure_time: time         # Hora de salida
    arrival_time: time           # Hora de llegada
    duration_hours: int          # Duración del vuelo
    class_flight: str            # "Economy", "Business"
    available_seats: int         # Asientos disponibles
    capacity: int                # Capacidad total
```

**Disponibilidad**: Los vuelos manejan disponibilidad directamente en el modelo principal.

### 3. 🏨 Alojamientos (Lodgments)
**Descripción**: Hoteles, hostales, apartamentos

**Características**:
- Ubicación
- Tipo de alojamiento
- Habitaciones con diferentes configuraciones
- Disponibilidad por fechas
- Capacidad de huéspedes

**Modelo**:
```python
class Lodgments(models.Model):
    name: str                    # "Hotel Plaza Mayor"
    description: str             # Descripción
    location: Location           # Ubicación
    type: str                    # "hotel", "hostel", "apartment"
    max_guests: int              # Máximo de huéspedes
    contact_phone: str           # Teléfono de contacto
    contact_email: str           # Email de contacto
    amenities: list              # ["WiFi", "Piscina", "Gimnasio"]
    date_checkin: date           # Fecha de check-in
    date_checkout: date          # Fecha de check-out
```

**Habitaciones**:
```python
class Room(models.Model):
    lodgment: Lodgments          # Alojamiento padre
    room_type: str               # "single", "double", "suite"
    name: str                    # "Habitación 101"
    capacity: int                # Capacidad de personas
    has_private_bathroom: bool   # Baño privado
    has_balcony: bool            # Balcón
    base_price_per_night: Decimal # Precio base por noche
    currency: str                # Moneda
```

**Disponibilidad de Habitaciones**:
```python
class RoomAvailability(models.Model):
    room: Room                   # Habitación
    start_date: date             # Fecha de inicio
    end_date: date               # Fecha de fin
    available_quantity: int      # Cantidad disponible
    max_quantity: int            # Máximo disponible
    price_override: Decimal      # Precio especial (opcional)
    currency: str                # Moneda
    is_blocked: bool             # Bloqueada
    minimum_stay: int            # Estancia mínima
```

### 4. 🚌 Transporte (Transportation)
**Descripción**: Buses, vans, traslados privados

**Características**:
- Origen y destino
- Tipo de transporte
- Capacidad de pasajeros
- Horarios específicos
- Precios variables

**Modelo**:
```python
class Transportation(models.Model):
    origin: Location             # Punto de origen
    destination: Location        # Punto de destino
    type: str                    # "bus", "van", "car", "shuttle"
    description: str             # Descripción del servicio
    notes: str                   # Notas adicionales
    capacity: int                # Capacidad de pasajeros
```

**Disponibilidad**:
```python
class TransportationAvailability(models.Model):
    transportation: Transportation # Transporte padre
    departure_date: date          # Fecha de salida
    departure_time: time          # Hora de salida
    arrival_date: date            # Fecha de llegada
    arrival_time: time            # Hora de llegada
    total_seats: int              # Total de asientos
    reserved_seats: int           # Asientos reservados
    price: Decimal                # Precio
    currency: str                 # Moneda
    state: str                    # "active", "cancelled"
```

---

## 📊 Sistema de Disponibilidad

### Concepto Central
La disponibilidad representa **instancias específicas** de un producto con:
- Fecha y horario concretos
- Stock disponible
- Precio específico
- Estado (activo, cancelado, etc.)

### ¿Por qué es necesaria?

#### Sin Sistema de Disponibilidad:
```
Producto: "Tour Machu Picchu"
- Precio: $50
- Cupos: 100
```
❌ **Problemas**:
- No distingue entre diferentes fechas
- No maneja precios variables
- No controla cupos por sesión
- No permite cancelaciones específicas

#### Con Sistema de Disponibilidad:
```
Producto: "Tour Machu Picchu"
├── Disponibilidad 1: 15/01/2024 09:00 - $50 - 20 cupos
├── Disponibilidad 2: 15/01/2024 14:00 - $45 - 15 cupos
├── Disponibilidad 3: 16/01/2024 09:00 - $50 - 25 cupos
└── Disponibilidad 4: 16/01/2024 14:00 - $45 - 10 cupos
```
✅ **Ventajas**:
- Control granular de inventario
- Precios diferenciados por horario
- Cancelaciones específicas
- Reservas precisas

### Identificadores Clave

#### 1. `product_metadata_id`
- **Qué es**: ID de la información comercial del producto
- **Ejemplo**: `45` = "Tour Machu Picchu" con precio base $50
- **Uso**: Identificar el producto general

#### 2. `availability_id`
- **Qué es**: ID de la disponibilidad específica
- **Ejemplo**: `100` = "Tour Machu Picchu el 15/01/2024 a las 14:00"
- **Uso**: Identificar la variante específica con fecha/horario

### Ejemplo Práctico
```json
{
    "product_metadata_id": 45,    // "Tour Machu Picchu"
    "availability_id": 100,       // "15/01/2024 14:00"
    "qty": 2,                     // 2 personas
    "unit_price": 45.0,           // $45 por persona
    "currency": "USD"
}
```

---

## 🔄 Flujo de Reservas

### 1. Verificación de Disponibilidad
```python
# 1. Verificar stock disponible
stock_info = check_activity_stock(availability_id=100, qty=2)

# Respuesta:
{
    "available": 15,        # Cupos disponibles
    "requested": 2,         # Cupos solicitados
    "sufficient": True,     # ¿Hay suficientes?
    "unit_price": 45.0,     # Precio unitario
    "currency": "USD"
}
```

### 2. Agregar al Carrito
```python
# 2. Reservar cupos y agregar al carrito
cart_item = add_item(
    cart=cart,
    metadata=product_metadata,
    availability_id=100,    # Disponibilidad específica
    qty=2,
    unit_price=45.0
)
```

### 3. Proceso de Checkout
```python
# 3. Convertir carrito en orden
order = checkout(cart, order_creator_fn)
```

### 4. Liberación de Stock
```python
# 4. Si se cancela o expira
release_activity(availability_id=100, qty=2)
```

---

## 🔌 API Reference

### Endpoints de Productos

#### Obtener Productos
```http
GET /api/products/
```

**Respuesta**:
```json
{
    "id": 45,
    "name": "Tour Machu Picchu",
    "description": "Visita guiada al sitio arqueológico",
    "unit_price": 50.0,
    "currency": "USD",
    "product_type": "activity",
    "supplier": {
        "id": 1,
        "name": "Peru Travel Agency"
    }
}
```

#### Verificar Disponibilidad
```http
GET /api/products/{metadata_id}/check/?qty=2&date=2024-01-15&start_time=14:00
```

**Respuesta**:
```json
{
    "remaining": 15,
    "enough": true,
    "unit_price": 45.0,
    "currency": "USD",
    "availability_id": 100
}
```

#### Listar Disponibilidades
```http
GET /api/products/{metadata_id}/availability/
```

**Respuesta**:
```json
[
    {
        "id": 100,
        "event_date": "2024-01-15",
        "start_time": "14:00:00",
        "total_seats": 20,
        "reserved_seats": 5,
        "price": 45.0,
        "currency": "USD",
        "state": "active"
    }
]
```

### Endpoints del Carrito

#### Agregar Item
```http
POST /api/cart/items/
```

**Body**:
```json
{
    "availability_id": 100,
    "product_metadata_id": 45,
    "qty": 2,
    "unit_price": 45.0,
    "config": {
        "special_requests": "Vegetariano"
    }
}
```

**Respuesta**:
```json
{
    "id": 1,
    "availability_id": 100,
    "product_metadata_id": 45,
    "qty": 2,
    "unit_price": 45.0,
    "currency": "USD",
    "config": {
        "special_requests": "Vegetariano"
    }
}
```

#### Obtener Carrito
```http
GET /api/cart/
```

**Respuesta**:
```json
{
    "id": 1,
    "user_id": 123,
    "status": "OPEN",
    "items_cnt": 2,
    "total": 90.0,
    "currency": "USD",
    "updated_at": "2024-01-15T10:30:00Z",
    "items": [
        {
            "id": 1,
            "availability_id": 100,
            "product_metadata_id": 45,
            "qty": 2,
            "unit_price": 45.0,
            "currency": "USD",
            "config": {}
        }
    ]
}
```

---

## 💡 Ejemplos Prácticos

### Ejemplo 1: Tour de Actividad
```python
# 1. Producto base
product_metadata = {
    "id": 45,
    "name": "Tour Machu Picchu",
    "unit_price": 50.0,
    "currency": "USD"
}

# 2. Disponibilidades específicas
availabilities = [
    {
        "id": 100,
        "event_date": "2024-01-15",
        "start_time": "09:00",
        "price": 50.0,
        "total_seats": 20,
        "reserved_seats": 5
    },
    {
        "id": 101,
        "event_date": "2024-01-15", 
        "start_time": "14:00",
        "price": 45.0,
        "total_seats": 15,
        "reserved_seats": 3
    }
]

# 3. Reserva específica
reservation = {
    "product_metadata_id": 45,    # Tour Machu Picchu
    "availability_id": 101,       # 15/01/2024 14:00
    "qty": 2,
    "unit_price": 45.0
}
```

### Ejemplo 2: Alojamiento con Habitaciones
```python
# 1. Alojamiento base
lodgment = {
    "id": 10,
    "name": "Hotel Plaza Mayor",
    "type": "hotel"
}

# 2. Habitaciones
rooms = [
    {
        "id": 50,
        "room_type": "single",
        "capacity": 1,
        "base_price_per_night": 80.0
    },
    {
        "id": 51,
        "room_type": "double", 
        "capacity": 2,
        "base_price_per_night": 120.0
    }
]

# 3. Disponibilidad de habitaciones
room_availabilities = [
    {
        "id": 200,
        "room_id": 50,
        "start_date": "2024-01-15",
        "end_date": "2024-01-17",
        "available_quantity": 5,
        "price_override": 90.0  # Precio especial
    }
]

# 4. Reserva
reservation = {
    "product_metadata_id": 10,    # Hotel Plaza Mayor
    "availability_id": 200,       # Habitación single 15-17 enero
    "qty": 1,
    "unit_price": 90.0
}
```

### Ejemplo 3: Vuelo
```python
# 1. Vuelo (maneja disponibilidad directamente)
flight = {
    "id": 30,
    "airline": "LATAM",
    "flight_number": "LA1234",
    "origin": "Lima",
    "destination": "Cusco",
    "departure_date": "2024-01-15",
    "departure_time": "08:00",
    "available_seats": 150,
    "capacity": 180
}

# 2. Reserva
reservation = {
    "product_metadata_id": 30,    # Vuelo LATAM LA1234
    "availability_id": 30,        # Mismo ID del vuelo
    "qty": 2,
    "unit_price": 120.0
}
```

---

## 🎯 Casos de Uso

### Caso 1: Reserva de Tour
**Escenario**: Cliente quiere reservar 2 cupos para el tour de Machu Picchu el 15 de enero a las 14:00

**Flujo**:
1. Cliente busca "Tour Machu Picchu"
2. Sistema muestra disponibilidades disponibles
3. Cliente selecciona: 15/01/2024 14:00 ($45)
4. Sistema verifica: 15 cupos disponibles
5. Cliente agrega al carrito: `availability_id=100`
6. Sistema reserva 2 cupos en esa disponibilidad
7. Checkout: Se crea orden con reserva específica

### Caso 2: Cancelación de Reserva
**Escenario**: Cliente cancela su reserva

**Flujo**:
1. Sistema identifica: `availability_id=100`
2. Libera 2 cupos de esa disponibilidad específica
3. Actualiza: `reserved_seats` de 5 a 3
4. Otros clientes pueden reservar esos cupos

### Caso 3: Precios Variables
**Escenario**: Diferentes precios por horario

**Configuración**:
- Mañana (09:00): $50 (demanda alta)
- Tarde (14:00): $45 (demanda media)
- Noche (18:00): $40 (demanda baja)

**Resultado**: Cada disponibilidad tiene su propio precio y control de stock.

### Caso 4: Capacidad Limitada
**Escenario**: Tour con cupos limitados por sesión

**Configuración**:
- Disponibilidad 1: 20 cupos máximos
- Disponibilidad 2: 15 cupos máximos
- Disponibilidad 3: 25 cupos máximos

**Ventaja**: Control granular de capacidad por sesión.

---

## 🔧 Consideraciones Técnicas

### Validaciones
- **Stock suficiente**: Verificar antes de reservar
- **Fechas válidas**: No permitir fechas pasadas
- **Precios positivos**: Validar precios mayores a 0
- **Cantidades válidas**: Verificar cantidades positivas

### Transacciones
- **Atomicidad**: Reservas y liberaciones en transacciones
- **Consistencia**: Mantener integridad del stock
- **Aislamiento**: Evitar condiciones de carrera

### Auditoría
- **Log de operaciones**: Registrar todas las reservas/liberaciones
- **Métricas**: Seguimiento de utilización
- **Historial**: Cambios en disponibilidad

### Performance
- **Índices**: En fechas y availability_id
- **Consultas optimizadas**: Evitar N+1 queries
- **Caché**: Para consultas frecuentes

---

## 📝 Resumen

El sistema de disponibilidad permite:

✅ **Control granular** de inventario por fecha/horario
✅ **Precios diferenciados** según demanda
✅ **Reservas precisas** con trazabilidad completa
✅ **Cancelaciones específicas** sin afectar otras disponibilidades
✅ **Escalabilidad** para múltiples productos y variantes

**Clave**: `availability_id` es el identificador que conecta el producto general con su variante específica, permitiendo un control preciso del inventario y las reservas. 