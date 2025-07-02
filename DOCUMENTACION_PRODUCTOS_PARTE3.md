# Documentación de Productos - Parte 3: Endpoints y Ejemplos de Uso

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

**Response**:
```json
{
  "id": 1,
  "precio_unitario": 150.0,
  "tipo_producto": "activity",
  "producto": {
    "id": 1,
    "name": "Tour por la Ciudad",
    "description": "Recorrido turístico por los principales puntos de interés",
    "location": {
      "country": "Argentina",
      "state": "Buenos Aires",
      "city": "Buenos Aires"
    },
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

**Ejemplo de Request**:
```http
GET /products/productos/?tipo=activity&precio_max=200&destino_id=1&ordering=precio
```

**Response**:
```json
[
  {
    "id": 1,
    "precio_unitario": 150.0,
    "tipo_producto": "activity",
    "producto": {
      "id": 1,
      "name": "Tour por la Ciudad",
      "description": "Recorrido turístico por los principales puntos de interés",
      "location": {
        "country": "Argentina",
        "state": "Buenos Aires",
        "city": "Buenos Aires"
      },
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
]
```

#### Obtener Producto Específico
```http
GET /products/productos/{id}/
```

**Response**:
```json
{
  "id": 1,
  "precio_unitario": 150.0,
  "tipo_producto": "activity",
  "producto": {
    "id": 1,
    "name": "Tour por la Ciudad",
    "description": "Recorrido turístico por los principales puntos de interés",
    "location": {
      "country": "Argentina",
      "state": "Buenos Aires",
      "city": "Buenos Aires"
    },
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

#### Listar Disponibilidades de Actividad
```http
GET /products/productos/{id}/availability/
```

**Response**:
```json
[
  {
    "id": 1,
    "activity_id": 1,
    "event_date": "2024-12-25",
    "start_time": "09:00:00",
    "total_seats": 20,
    "reserved_seats": 5,
    "price": 150.0,
    "currency": "USD",
    "state": "active"
  }
]
```

#### Listar Disponibilidades de Transporte
```http
GET /products/productos/{id}/transportation-availability/
```

**Response**:
```json
[
  {
    "id": 1,
    "transportation_id": 1,
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
```

### 2. Endpoints de Proveedores

#### Listar Proveedores
```http
GET /suppliers/
```

**Response**:
```json
[
  {
    "id": 1,
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
]
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

**Response**:
```json
[
  {
    "id": 1,
    "nombre": "Paquete A"
  },
  {
    "id": 2,
    "nombre": "Paquete B"
  }
]
```

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
import requests

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

response = requests.post("http://localhost:8000/products/productos/crear/", json=activity_data)
print(response.json())
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

response = requests.get("http://localhost:8000/products/productos/", params=search_params)
lodgments = response.json()
print(f"Se encontraron {len(lodgments)} alojamientos")
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

response = requests.post("http://localhost:8000/products/productos/alojamiento-completo/", json=package_data)
print(response.json())
```

### 4. Consultar Disponibilidad

```python
# Ejemplo de consulta de disponibilidad
product_id = 123
response = requests.get(f"http://localhost:8000/products/productos/{product_id}/availability/")
availabilities = response.json()

# Filtrar por fecha específica
available_slots = [
    av for av in availabilities 
    if av["event_date"] == "2024-12-25" and av["total_seats"] > av["reserved_seats"]
]

print(f"Hay {len(available_slots)} horarios disponibles para el 25 de diciembre")
```

### 5. Crear un Vuelo

```python
# Ejemplo de creación de vuelo
flight_data = {
    "tipo_producto": "flight",
    "precio_unitario": 300.0,
    "supplier_id": 1,
    "producto": {
        "airline": "Aerolíneas Argentinas",
        "flight_number": "AR1234",
        "origin_id": 1,
        "destination_id": 2,
        "departure_date": "2024-12-25",
        "departure_time": "10:00:00",
        "arrival_date": "2024-12-25",
        "arrival_time": "12:00:00",
        "duration_hours": 2,
        "class_flight": "Economy",
        "available_seats": 150,
        "luggage_info": "1 maleta de 23kg incluida",
        "aircraft_type": "Boeing 737",
        "terminal": "A",
        "gate": "15"
    }
}

response = requests.post("http://localhost:8000/products/productos/crear/", json=flight_data)
print(response.json())
```

### 6. Crear un Servicio de Transporte

```python
# Ejemplo de creación de transporte
transport_data = {
    "tipo_producto": "transportation",
    "precio_unitario": 50.0,
    "supplier_id": 1,
    "producto": {
        "origin_id": 1,
        "destination_id": 2,
        "type": "bus",
        "description": "Servicio de bus interurbano con wifi y aire acondicionado",
        "notes": "Incluye equipaje de mano y una maleta grande",
        "capacity": 45
    }
}

response = requests.post("http://localhost:8000/products/productos/crear/", json=transport_data)
print(response.json())
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