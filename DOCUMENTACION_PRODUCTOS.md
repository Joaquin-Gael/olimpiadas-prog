# Documentación de la Aplicación de Productos

## Índice
1. [Arquitectura General](#arquitectura-general)
2. [Modelos de Datos](#modelos-de-datos)
3. [Lógica de Negocio](#lógica-de-negocio)
4. [Validaciones y Schemas](#validaciones-y-schemas)
5. [Endpoints y API](#endpoints-y-api)
6. [Filtros y Búsquedas](#filtros-y-búsquedas)
7. [Ejemplos de Uso](#ejemplos-de-uso)

---

## Arquitectura General

La aplicación de productos utiliza un patrón de **Generic Foreign Key** para manejar diferentes tipos de productos de manera flexible. La estructura principal se basa en:

### Componentes Principales

1. **ProductsMetadata**: Modelo central que actúa como wrapper para todos los productos
2. **Modelos Específicos**: Activities, Flights, Lodgment, Transportation
3. **Modelos de Disponibilidad**: Cada producto tiene su propio modelo de disponibilidad
4. **Sistema de Ubicaciones**: Modelo Location compartido entre todos los productos

### Patrón de Diseño

```
ProductsMetadata (Generic Foreign Key)
├── Activities + ActivityAvailability
├── Flights + FlightAvailability  
├── Lodgment + Room + RoomAvailability
└── Transportation + TransportationAvailability
```

---

## Modelos de Datos

### 1. ProductsMetadata (Modelo Central)

**Propósito**: Actúa como wrapper para todos los productos usando Generic Foreign Key.

```python
class ProductsMetadata(models.Model):
    id = models.AutoField("product_metadata_id", primary_key=True)
    supplier = models.ForeignKey(Suppliers, on_delete=models.PROTECT)
    content_type_id = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey("content_type_id", "object_id")
    precio_unitario = models.FloatField(validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
```

**Características**:
- **Generic Foreign Key**: Permite referenciar cualquier tipo de producto
- **Soft Delete**: Implementa eliminación lógica con `deleted_at`
- **ActiveManager**: Manager personalizado para filtrar registros activos
- **Precio Unitario**: Precio base del producto

### 2. Activities (Actividades)

**Propósito**: Representa actividades turísticas como tours, excursiones, etc.

```python
class Activities(models.Model):
    id = models.AutoField("activity_id", primary_key=True)
    name = models.CharField(max_length=128)
    description = models.TextField()
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    date = models.DateField()
    start_time = models.TimeField()
    duration_hours = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(24)])
    include_guide = models.BooleanField()
    maximum_spaces = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    difficulty_level = models.CharField(max_length=16, choices=DifficultyLevel.choices())
    language = models.CharField(max_length=32)
    available_slots = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
```

**Enums Relacionados**:
```python
class DifficultyLevel(Enum):
    VERY_EASY = "Very Easy"
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    VERY_HARD = "Very Hard"
    EXTREME = "Extreme"
```

### 3. Flights (Vuelos)

**Propósito**: Representa vuelos comerciales con información detallada.

```python
class Flights(models.Model):
    id = models.AutoField("flight_id", primary_key=True)
    airline = models.CharField(max_length=32)
    flight_number = models.CharField(max_length=16)
    origin = models.ForeignKey(Location, related_name="flights_departing", on_delete=models.PROTECT)
    destination = models.ForeignKey(Location, related_name="flights_arriving", on_delete=models.PROTECT)
    departure_date = models.DateField()
    departure_time = models.TimeField()
    arrival_date = models.DateField()
    arrival_time = models.TimeField()
    duration_hours = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(192)])
    class_flight = models.CharField(max_length=32, choices=ClassFlight.choices())
    available_seats = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(500)])
    luggage_info = models.CharField(max_length=128)
    aircraft_type = models.CharField(max_length=32)
    terminal = models.CharField(max_length=16, blank=True)
    gate = models.CharField(max_length=8, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
```

**Enums Relacionados**:
```python
class ClassFlight(Enum):
    BASIC_ECONOMY = "Basic Economy"
    ECONOMY = "Economy"
    PREMIUM_ECONOMY = "Premium Economy"
    BUSINESS = "Business Class"
    FIRST = "First Class"
```

### 4. Lodgment (Alojamientos)

**Propósito**: Representa diferentes tipos de alojamientos con sistema de habitaciones.

```python
class Lodgment(models.Model):
    id = models.AutoField("lodgment_id", primary_key=True)
    name = models.CharField(max_length=128, db_index=True)
    description = models.TextField(blank=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, db_index=True)
    type = models.CharField(max_length=32, choices=LodgmentType.choices())
    max_guests = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(50)])
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    amenities = models.JSONField(default=list, blank=True)
    date_checkin = models.DateField(db_index=True)
    date_checkout = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
```

**Enums Relacionados**:
```python
class LodgmentType(Enum):
    HOTEL = "hotel"
    HOSTEL = "hostel"
    APARTMENT = "apartment"
    HOUSE = "house"
    CABIN = "cabin"
    RESORT = "resort"
    BED_AND_BREAKFAST = "bed_and_breakfast"
    VILLA = "villa"
    CAMPING = "camping"
```

### 5. Transportation (Transporte)

**Propósito**: Representa servicios de transporte terrestre.

```python
class Transportation(models.Model):
    id = models.AutoField(primary_key=True)
    origin = models.ForeignKey("Location", related_name="transport_departures", on_delete=models.PROTECT)
    destination = models.ForeignKey("Location", related_name="transport_arrivals", on_delete=models.PROTECT)
    type = models.CharField(max_length=16, choices=TransportationType.choices, default=TransportationType.BUS)
    description = models.TextField()
    notes = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
```

**Enums Relacionados**:
```python
class TransportationType(models.TextChoices):
    BUS = "bus", "Bus"
    VAN = "van", "Van"
    CAR = "car", "Auto privado"
    SHUTTLE = "shuttle", "Shuttle"
    TRAIN = "train", "Tren"
    OTHER = "other", "Otro"
```

---

## Lógica de Negocio

### 1. Sistema de Disponibilidad

Cada tipo de producto tiene su propio modelo de disponibilidad:

#### ActivityAvailability
```python
class ActivityAvailability(models.Model):
    activity = models.ForeignKey("Activities", on_delete=models.CASCADE, related_name="availabilities")
    event_date = models.DateField()
    start_time = models.TimeField()
    total_seats = models.IntegerField(validators=[MinValueValidator(0)])
    reserved_seats = models.IntegerField(validators=[MinValueValidator(0)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8)
    state = models.CharField(max_length=32, default="active")
```

#### RoomAvailability
```python
class RoomAvailability(models.Model):
    room = models.ForeignKey(Room, related_name="availabilities", on_delete=models.CASCADE)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    available_quantity = models.IntegerField(validators=[MinValueValidator(0)])
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    is_blocked = models.BooleanField(default=False)
    minimum_stay = models.IntegerField(validators=[MinValueValidator(1)], default=1)
```

#### TransportationAvailability
```python
class TransportationAvailability(models.Model):
    transportation = models.ForeignKey(Transportation, related_name="availabilities", on_delete=models.CASCADE)
    departure_date = models.DateField()
    departure_time = models.TimeField()
    arrival_date = models.DateField()
    arrival_time = models.TimeField()
    total_seats = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    reserved_seats = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    state = models.CharField(max_length=32, default="active")
```

### 2. Sistema de Precios

- **Precio Base**: Definido en `ProductsMetadata.precio_unitario`
- **Precio Override**: Disponible en `RoomAvailability.price_override`
- **Cálculo de Precio Final**: `get_final_price(discount_percent=0)`

### 3. Validaciones de Negocio

#### Fechas
- Las fechas no pueden estar en el pasado
- Las fechas de llegada deben ser posteriores a las de salida
- Las fechas de checkout deben ser posteriores a las de checkin

#### Capacidad
- Los asientos reservados no pueden exceder el total
- Las cantidades disponibles no pueden ser negativas
- Capacidades mínimas y máximas según el tipo de producto

#### Precios
- Los precios no pueden ser negativos
- Validaciones de rangos específicos por tipo de producto

---

## Validaciones y Schemas

### 1. Schemas de Entrada (Create)

#### ActivityCreate
```python
class ActivityCreate(BaseSchema):
    name: str
    description: str
    location_id: int
    date: date
    start_time: time
    duration_hours: int = Field(..., ge=0, le=24)
    include_guide: bool
    maximum_spaces: int = Field(..., ge=0, le=100)
    difficulty_level: Literal["Very Easy", "Easy", "Medium", "Hard", "Very Hard", "Extreme"]
    language: str
    available_slots: int = Field(..., ge=0, le=100)

    @validator("date")
    def validate_date(cls, v):
        if v < date.today():
            raise ValueError("La fecha de la actividad no puede estar en el pasado.")
        return v
```

#### FlightCreate
```python
class FlightCreate(BaseSchema):
    airline: str
    flight_number: str
    origin_id: int
    destination_id: int
    departure_date: date
    departure_time: time
    arrival_date: date
    arrival_time: time
    duration_hours: int = Field(..., ge=0, le=192)
    class_flight: Literal["Basic Economy", "Economy", "Premium Economy", "Business Class", "First Class"]
    available_seats: int = Field(..., ge=0, le=500)
    luggage_info: str
    aircraft_type: str
    terminal: Optional[str] = None
    gate: Optional[str] = None
    notes: Optional[str] = None
```

### 2. Schemas de Salida (Output)

#### ProductsMetadataOut
```python
class ProductsMetadataOut(BaseSchema):
    id: int
    precio_unitario: float
    tipo_producto: Literal["activity", "flight", "lodgment", "transportation"]
    producto: Union[ActivityOut, FlightOut, LodgmentOut, TransportationOut]
```

### 3. Validaciones Específicas

#### Validaciones de Fechas
```python
@validator("event_date")
def validate_event_date(cls, v):
    if v < date.today():
        raise ValueError("Event date cannot be in the past.")
    return v
```

#### Validaciones de Capacidad
```python
@validator("reserved_seats")
def validate_reserved_seats(cls, v, values):
    if "total_seats" in values and v > values["total_seats"]:
        raise ValueError("Reserved seats cannot exceed total seats.")
    return v
```

#### Validaciones de Precios
```python
@validator("precio_unitario")
def validate_precio(cls, v):
    if v < 0:
        raise ValueError("El precio no puede ser negativo")
    return v
```

---

## Endpoints y API

### 1. Endpoints de Productos

#### Crear Producto Básico
```http
POST /products/productos/crear/
```

**Request Body**:
```json
{
  "tipo_producto": "activity",
  "precio_unitario": 150.0,
  "supplier_id": 1,
  "producto": {
    "name": "Tour por la Ciudad",
    "description": "Recorrido turístico por los principales puntos de interés",
    "location_id": 1,
    "date": "2024-12-25",
    "start_time": "09:00:00",
    "duration_hours": 4,
    "include_guide": true,
    "maximum_spaces": 20,
    "difficulty_level": "Easy",
    "language": "Español",
    "available_slots": 15
  }
}
```

#### Crear Actividad Completa
```http
POST /products/productos/actividad-completa/
```

**Request Body**:
```json
{
  "name": "Tour por la Ciudad",
  "description": "Recorrido turístico por los principales puntos de interés",
  "location_id": 1,
  "date": "2024-12-25",
  "start_time": "09:00:00",
  "duration_hours": 4,
  "include_guide": true,
  "maximum_spaces": 20,
  "difficulty_level": "Easy",
  "language": "Español",
  "available_slots": 15,
  "supplier_id": 1,
  "precio_unitario": 150.0,
  "currency": "USD",
  "availabilities": [
    {
      "event_date": "2024-12-25",
      "start_time": "09:00:00",
      "total_seats": 20,
      "reserved_seats": 5,
      "price": 150.0,
      "currency": "USD"
    }
  ]
}
```

#### Crear Alojamiento Completo
```http
POST /products/productos/alojamiento-completo/
```

**Request Body**:
```json
{
  "precio_unitario": 200.0,
  "supplier_id": 1,
  "name": "Hotel Central",
  "description": "Hotel céntrico con todas las comodidades",
  "location_id": 1,
  "type": "hotel",
  "max_guests": 50,
  "contact_phone": "+1234567890",
  "contact_email": "info@hotelcentral.com",
  "amenities": ["wifi", "parking", "restaurant"],
  "date_checkin": "2024-12-20",
  "date_checkout": "2024-12-25",
  "rooms": [
    {
      "room_type": "double",
      "name": "Habitación 101",
      "description": "Habitación doble con vista a la ciudad",
      "capacity": 2,
      "has_private_bathroom": true,
      "has_balcony": true,
      "has_air_conditioning": true,
      "has_wifi": true,
      "base_price_per_night": 100.0,
      "currency": "USD",
      "availabilities": [
        {
          "start_date": "2024-12-20",
          "end_date": "2024-12-25",
          "available_quantity": 5,
          "price_override": null,
          "currency": "USD",
          "is_blocked": false,
          "minimum_stay": 1
        }
      ]
    }
  ]
}
```

#### Crear Transporte Completo
```http
POST /products/productos/transporte-completo/
```

**Request Body**:
```json
{
  "precio_unitario": 50.0,
  "supplier_id": 1,
  "origin_id": 1,
  "destination_id": 2,
  "type": "bus",
  "description": "Servicio de bus interurbano",
  "notes": "Incluye equipaje de mano",
  "capacity": 45,
  "availabilities": [
    {
      "departure_date": "2024-12-25",
      "departure_time": "08:00:00",
      "arrival_date": "2024-12-25",
      "arrival_time": "10:00:00",
      "total_seats": 45,
      "reserved_seats": 10,
      "price": 50.0,
      "currency": "USD",
      "state": "active"
    }
  ]
}
```

#### Listar Productos
```http
GET /products/productos/
```

**Query Parameters**:
- `tipo`: Tipo de producto (activity, flight, lodgment, transportation)
- `precio_min`: Precio mínimo
- `precio_max`: Precio máximo
- `destino_id`: ID de ubicación de destino
- `origen_id`: ID de ubicación de origen
- `fecha_min`: Fecha mínima
- `fecha_max`: Fecha máxima
- `ordering`: Ordenamiento (precio, -precio, fecha, -fecha, etc.)

#### Obtener Producto Específico
```http
GET /products/productos/{id}/
```

#### Listar Disponibilidades de Actividad
```http
GET /products/productos/{id}/availability/
```

#### Listar Disponibilidades de Transporte
```http
GET /products/productos/{id}/transportation-availability/
```

### 2. Endpoints de Proveedores

#### Listar Proveedores
```http
GET /suppliers/
```

#### Crear Proveedor
```http
POST /suppliers/
```

**Request Body**:
```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "organization_name": "Turismo ABC",
  "description": "Empresa de turismo especializada en tours",
  "street": "Av. Principal",
  "street_number": 123,
  "city": "Buenos Aires",
  "country": "Argentina",
  "email": "juan@turismoabc.com",
  "telephone": "+541123456789",
  "website": "https://turismoabc.com"
}
```

### 3. Endpoints de Paquetes

#### Listar Paquetes
```http
GET /package/paquetes/
```

### 4. Endpoints de Cotización y Chequeo Rápido

#### Cotizar Habitación (quote_room)
```http
GET /products/room/{room_id}/quote/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&qty=1
```

**Descripción:**
Devuelve el precio final para reservar una o más habitaciones en un rango de fechas, incluyendo impuestos y validando cupo y estadía mínima.

**Parámetros obligatorios:**
- `start_date`: Fecha de check-in (YYYY-MM-DD)
- `end_date`: Fecha de check-out (exclusiva, YYYY-MM-DD)
- `qty`: Cantidad de habitaciones

**Respuesta 200:**
```json
{
  "unit_price": 120.00,      // por noche
  "nights": 3,               // end-start
  "rooms": 2,                // qty
  "subtotal": 720.00,        // unit×nights×rooms
  "taxes": 151.20,           // si aplica 21 % IVA
  "total_price": 871.20,     // subtotal + taxes
  "currency": "USD",
  "availability_id": 57      // para reservar después
}
```
**Errores clave:**
- 404: No existe disponibilidad que cubra el rango
- 409: No hay cupo suficiente (`{"remaining": 1}`)
- 422: Fechas inválidas o estadía menor al mínimo

---

#### Chequeo Rápido de Disponibilidad (check_*)

**Descripción:**
Permite al carrito o frontend consultar rápidamente si hay cupo suficiente para una reserva, sin bloquear stock ni modificar la base de datos. Responde con el cupo disponible, si alcanza, el precio unitario y la moneda.

**Respuesta uniforme:**
```json
{
  "remaining": 7,        // cupos que quedarían libres
  "enough": true,        // ¿alcanza qty?
  "unit_price": 120.00,  // precio por unidad/noche/asiento
  "currency": "USD",
  "availability_id": 57  // el ID que luego usará reserve_*
}
```
- Si no alcanza el stock → HTTP 409 (Conflict) con `"enough": false`.
- Si la disponibilidad no existe → HTTP 404.
- Validaciones de parámetros mal formados → HTTP 422.

**Rutas y parámetros por tipo:**

| Tipo           | Ruta                                       | Parámetros obligatorios                                     |
| -------------- | ------------------------------------------ | ----------------------------------------------------------- |
| Actividad      | `/products/{metadata_id}/check/`           | `qty`, `date`, `start_time`                                 |
| Transporte     | `/products/{metadata_id}/transport/check/` | `qty`, `date` (salida), `time` (salida)                    |
| Vuelo          | `/products/{metadata_id}/flight/check/`    | `qty`                                                      |
| Habitación     | `/products/room/{room_id}/check/`          | `qty`, `start_date`, `end_date`                             |

**Ejemplo de respuesta (200):**
```json
{
  "remaining": 3,
  "enough": true,
  "unit_price": 150.0,
  "currency": "USD",
  "availability_id": 42
}
```
**Ejemplo de respuesta (409):**
```json
{
  "remaining": 1,
  "enough": false,
  "unit_price": 150.0,
  "currency": "USD",
  "availability_id": 42
}
```

**Notas:**
- El campo `unit_price` para vuelos y currency se obtiene de `ProductsMetadata`.
- No se bloquea ni reserva stock, solo lectura.
- El campo `availability_id` es el que debe usarse luego para reservar.

---

## Endpoint PATCH /products/{id}/ — Actualización anidada (opción B)

A partir de la versión actual, el endpoint PATCH permite actualizar tanto los campos planos de metadata como sub-estructuras anidadas (habitaciones, disponibilidades, vuelos, transportes) en un solo request.

### ¿Qué se puede actualizar?
- **Campos planos**: unit_price, currency, is_active, etc.
- **Alojamientos**: lista de habitaciones (`rooms`) y disponibilidades (`availabilities`)
- **Actividades**: lista de disponibilidades (`availabilities`)
- **Vuelos**: lista de vuelos (`flights`)
- **Transportes**: lista de transportes (`transportations`)

### Ejemplo de request para alojamiento
```json
PATCH /products/42/
{
  "unit_price": 920,
  "currency": "USD",
  "rooms": [
    { "id": 7, "base_price_per_night": 110, "is_active": true },
    { "id": 8, "name": "Suite Deluxe" }
  ],
  "availabilities": [
    { "id": 15, "available_quantity": 2 }
  ]
}
```

### Ejemplo de request para actividad
```json
PATCH /products/99/
{
  "availabilities": [
    { "id": 21, "total_seats": 30, "price": 150 }
  ]
}
```

### Ejemplo de request para vuelo
```json
PATCH /products/55/
{
  "flights": [
    { "id": 3, "available_seats": 120, "notes": "Vuelo reprogramado" }
  ]
}
```

### Ejemplo de request para transporte
```json
PATCH /products/77/
{
  "transportations": [
    { "id": 5, "capacity": 40, "is_active": false }
  ]
}
```

### Notas importantes
- **Atomicidad**: Si alguna sub-actualización falla, ninguna modificación se graba (transacción completa).
- **Validación**: No se permite cambiar el `id` de los sub-objetos. Si se envía un campo no permitido, se responde con 422 y mensaje claro.
- **Compatibilidad**: Los campos planos y anidados pueden enviarse juntos o por separado.
- **Documentación OpenAPI**: Los schemas de entrada reflejan todos los campos y sub-estructuras permitidas.

---

## Filtros y Búsquedas

### 1. Filtros Principales

```python
class ProductosFiltro(Schema):
    # Filtros básicos
    tipo: Optional[Literal["activity", "flight", "lodgment", "transportation"]] = None
    search: Optional[str] = None
    supplier_id: Optional[int] = None
    
    # Filtros de ubicación
    destino_id: Optional[int] = None
    origen_id: Optional[int] = None
    location_id: Optional[int] = None
    
    # Filtros de fechas
    fecha_min: Optional[date] = None
    fecha_max: Optional[date] = None
    fecha_checkin: Optional[date] = None
    fecha_checkout: Optional[date] = None
    
    # Filtros de precio
    precio_min: Optional[float] = Field(None, ge=0)
    precio_max: Optional[float] = Field(None, ge=0)
    
    # Filtros de disponibilidad
    disponibles_solo: Optional[bool] = Field(True)
    capacidad_min: Optional[int] = Field(None, ge=1)
    capacidad_max: Optional[int] = Field(None, ge=1)
    
    # Ordenamiento
    ordering: Optional[str] = None
```

### 2. Filtros Específicos por Tipo

#### Filtros de Actividades
```python
class FiltroActividades(Schema):
    nivel_dificultad: Optional[Literal["Very Easy", "Easy", "Medium", "Hard", "Very Hard", "Extreme"]] = None
    incluye_guia: Optional[bool] = None
    idioma: Optional[str] = None
    duracion_min: Optional[int] = Field(None, ge=0, le=24)
    duracion_max: Optional[int] = Field(None, ge=0, le=24)
    fecha_especifica: Optional[date] = None
    hora_inicio: Optional[time] = None
```

#### Filtros de Vuelos
```python
class FiltroVuelos(Schema):
    aerolinea: Optional[str] = None
    clase_vuelo: Optional[Literal["Basic Economy", "Economy", "Premium Economy", "Business Class", "First Class"]] = None
    duracion_vuelo_min: Optional[int] = Field(None, ge=0)
    duracion_vuelo_max: Optional[int] = Field(None, ge=0)
    escala_directa: Optional[bool] = None
    terminal: Optional[str] = None
```

#### Filtros de Alojamientos
```python
class FiltroAlojamientos(Schema):
    tipo_alojamiento: Optional[Literal["hotel", "hostel", "apartment", "house", "cabin", "resort", "bed_and_breakfast", "villa", "camping"]] = None
    tipo_habitacion: Optional[Literal["single", "double", "triple", "quadruple", "suite", "family", "dormitory", "studio"]] = None
    huespedes_min: Optional[int] = Field(None, ge=1)
    huespedes_max: Optional[int] = Field(None, ge=1)
    noches_min: Optional[int] = Field(None, ge=1)
    amenidades: Optional[List[str]] = None
    bano_privado: Optional[bool] = None
    balcon: Optional[bool] = None
    aire_acondicionado: Optional[bool] = None
    wifi: Optional[bool] = None
```

### 3. Ordenamiento

```python
order_map = {
    "precio": "precio_unitario",
    "-precio": "-precio_unitario",
    "fecha": "activity__date",
    "-fecha": "-activity__date",
    "nombre": "activity__name",
    "-nombre": "-activity__name",
    "rating": "precio_unitario",  # Placeholder
    "-rating": "-precio_unitario",
    "popularidad": "precio_unitario",  # Placeholder
    "-popularidad": "-precio_unitario",
}
```

---

## Ejemplos de Uso

### 1. Crear una Actividad Turística

```python
# Ejemplo de creación de actividad
activity_data = {
    "tipo_producto": "activity",
    "precio_unitario": 120.0,
    "supplier_id": 1,
    "producto": {
        "name": "Tour por el Centro Histórico",
        "description": "Recorrido guiado por los monumentos más importantes",
        "location_id": 1,
        "date": "2024-12-25",
        "start_time": "14:00:00",
        "duration_hours": 3,
        "include_guide": True,
        "maximum_spaces": 15,
        "difficulty_level": "Easy",
        "language": "Español",
        "available_slots": 12
    }
}

response = requests.post("/products/productos/crear/", json=activity_data)
```

### 2. Buscar Alojamientos Disponibles

```python
# Ejemplo de búsqueda de alojamientos
search_params = {
    "tipo": "lodgment",
    "destino_id": 1,
    "fecha_checkin": "2024-12-20",
    "fecha_checkout": "2024-12-25",
    "huespedes_min": 2,
    "precio_max": 200.0,
    "amenidades": ["wifi", "parking"],
    "ordering": "precio"
}

response = requests.get("/products/productos/", params=search_params)
```

### 3. Crear un Paquete Completo

```python
# Ejemplo de creación de paquete completo
package_data = {
    "precio_unitario": 500.0,
    "supplier_id": 1,
    "name": "Paquete Fin de Semana",
    "description": "Incluye alojamiento, transporte y actividad",
    "location_id": 1,
    "type": "hotel",
    "max_guests": 4,
    "contact_phone": "+1234567890",
    "contact_email": "info@paquete.com",
    "amenities": ["wifi", "breakfast"],
    "date_checkin": "2024-12-20",
    "date_checkout": "2024-12-22",
    "rooms": [
        {
            "room_type": "family",
            "name": "Suite Familiar",
            "capacity": 4,
            "base_price_per_night": 200.0,
            "availabilities": [
                {
                    "start_date": "2024-12-20",
                    "end_date": "2024-12-22",
                    "available_quantity": 2,
                    "minimum_stay": 2
                }
            ]
        }
    ]
}

response = requests.post("/products/productos/alojamiento-completo/", json=package_data)
```

### 4. Consultar Disponibilidad

```python
# Ejemplo de consulta de disponibilidad
product_id = 123
response = requests.get(f"/products/productos/{product_id}/availability/")
availabilities = response.json()

# Filtrar por fecha específica
available_slots = [
    av for av in availabilities 
    if av["event_date"] == "2024-12-25" and av["total_seats"] > av["reserved_seats"]
]
```

---

## Consideraciones Técnicas

### 1. Performance

- **Indexes**: Los modelos incluyen índices en campos frecuentemente consultados
- **Select Related**: Uso de `select_related` y `prefetch_related` para optimizar consultas
- **Paginación**: Implementación de paginación para listas grandes

### 2. Seguridad

- **Validaciones**: Validaciones exhaustivas en modelos y schemas
- **Soft Delete**: Eliminación lógica para mantener integridad referencial
- **Transacciones**: Uso de transacciones atómicas para operaciones complejas

### 3. Escalabilidad

- **Generic Foreign Key**: Permite agregar nuevos tipos de productos fácilmente
- **Modularidad**: Separación clara entre diferentes tipos de productos
- **Extensibilidad**: Fácil agregado de nuevos campos y funcionalidades

### 4. Mantenibilidad

- **Código Limpio**: Estructura clara y bien documentada
- **Separación de Responsabilidades**: Cada modelo tiene su propósito específico
- **Reutilización**: Schemas y validaciones reutilizables

---

## Conclusión

La aplicación de productos está diseñada con una arquitectura robusta y escalable que permite manejar diferentes tipos de productos turísticos de manera eficiente. El uso de Generic Foreign Keys, sistemas de disponibilidad específicos y validaciones exhaustivas garantizan la integridad de los datos y la flexibilidad del sistema.

La API REST proporciona endpoints completos para todas las operaciones CRUD, con soporte para filtros avanzados y búsquedas complejas. Los schemas de validación aseguran que los datos ingresados cumplan con las reglas de negocio establecidas. 