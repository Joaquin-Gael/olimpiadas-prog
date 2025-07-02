# Documentación de Productos - Parte 2: Lógica de Negocio y Validaciones

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

#### LodgmentCreate
```python
class LodgmentCreate(BaseSchema):
    name: str = Field(..., max_length=128)
    description: Optional[str] = None
    location_id: int
    type: Literal["hotel", "hostel", "apartment", "house", "cabin", "resort", "bed_and_breakfast", "villa", "camping"]
    max_guests: int = Field(..., ge=1, le=50)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[EmailStr] = None
    amenities: List[str] = Field(default_factory=list)
    date_checkin: date
    date_checkout: date

    @validator("date_checkin")
    def validate_checkin_date(cls, v):
        if v < date.today():
            raise ValueError("La fecha de check-in no puede estar en el pasado.")
        return v

    @validator("date_checkout")
    def validate_checkout_date(cls, v, values):
        if "date_checkin" in values and v <= values["date_checkin"]:
            raise ValueError("La fecha de check-out debe ser posterior a la fecha de check-in.")
        return v
```

#### TransportationCreate
```python
class TransportationCreate(BaseSchema):
    origin_id: int
    destination_id: int
    type: TransportationType = TransportationType.bus
    description: str
    notes: Optional[str] = ""
    capacity: int = Field(..., gt=0, le=100)

    @validator("description")
    def desc_required(cls, v):
        if not v or not v.strip():
            raise ValueError("La descripción es obligatoria")
        return v
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

#### ActivityOut
```python
class ActivityOut(BaseSchema):
    id: int
    name: str
    description: str
    location: LocationOut
    date: date
    start_time: time
    duration_hours: int
    include_guide: bool
    maximum_spaces: int
    difficulty_level: str
    language: str
    available_slots: int
```

#### FlightOut
```python
class FlightOut(BaseSchema):
    id: int
    airline: str
    flight_number: str
    origin: LocationOut
    destination: LocationOut
    departure_date: date
    departure_time: time
    arrival_date: date
    arrival_time: time
    duration_hours: int
    class_flight: str
    available_seats: int
    luggage_info: str
    aircraft_type: str
    terminal: Optional[str]
    gate: Optional[str]
    notes: Optional[str]
```

### 3. Validaciones Específicas

#### Validaciones de Fechas
```python
@validator("event_date")
def validate_event_date(cls, v):
    if v < date.today():
        raise ValueError("Event date cannot be in the past.")
    return v

@validator("departure_date")
def validate_departure_date(cls, v):
    if v < date.today():
        raise ValueError("Departure date cannot be in the past.")
    return v

@validator("arrival_date")
def validate_arrival_date(cls, v, values):
    if "departure_date" in values and v < values["departure_date"]:
        raise ValueError("Arrival date must be after departure date.")
    return v
```

#### Validaciones de Capacidad
```python
@validator("reserved_seats")
def validate_reserved_seats(cls, v, values):
    if "total_seats" in values and v > values["total_seats"]:
        raise ValueError("Reserved seats cannot exceed total seats.")
    return v

@validator("available_slots")
def validate_available_slots(cls, v, values):
    if "maximum_spaces" in values and v > values["maximum_spaces"]:
        raise ValueError("Available slots cannot exceed maximum spaces.")
    return v
```

#### Validaciones de Precios
```python
@validator("precio_unitario")
def validate_precio(cls, v):
    if v < 0:
        raise ValueError("El precio no puede ser negativo")
    return v

@validator("price")
def validate_price(cls, v):
    if v <= 0:
        raise ValueError("Price must be greater than zero")
    return v
```

### 4. Schemas de Disponibilidad

#### ActivityAvailabilityCreate
```python
class ActivityAvailabilityCreate(BaseModel):
    event_date: date
    start_time: time
    total_seats: int = Field(..., ge=1, description="Total number of seats available")
    reserved_seats: int = Field(..., ge=0, description="Number of already reserved seats")
    price: float = Field(..., gt=0, description="Price per person")
    currency: str = Field(..., max_length=8, description="Currency code, e.g., USD")
    state: Optional[str] = Field(default="active")

    @validator("event_date")
    def validate_event_date(cls, v):
        if v < date.today():
            raise ValueError("Event date cannot be in the past.")
        return v

    @validator("reserved_seats")
    def validate_reserved_seats(cls, v, values):
        if "total_seats" in values and v > values["total_seats"]:
            raise ValueError("Reserved seats cannot exceed total seats.")
        return v
```

#### RoomAvailabilityCreate
```python
class RoomAvailabilityCreate(BaseSchema):
    room_id: int
    start_date: date
    end_date: date
    available_quantity: int = Field(..., ge=0)
    price_override: Optional[float] = Field(None, gt=0)
    currency: str = Field(default="USD", max_length=3)
    is_blocked: bool = False
    minimum_stay: int = Field(default=1, ge=1)

    @validator("start_date")
    def validate_start_date(cls, v):
        if v < date.today():
            raise ValueError("Start date cannot be in the past.")
        return v

    @validator("end_date")
    def validate_end_date(cls, v, values):
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date.")
        return v
```

#### TransportationAvailabilityCreate
```python
class TransportationAvailabilityCreate(BaseModel):
    departure_date: date
    departure_time: time
    arrival_date: date
    arrival_time: time
    total_seats: int = Field(..., gt=0, description="Total number of seats available")
    reserved_seats: int = Field(..., ge=0, description="Number of already reserved seats")
    price: float = Field(..., gt=0, description="Price per person")
    currency: str = Field(..., max_length=8, description="Currency code, e.g., USD")
    state: Optional[str] = Field(default="active")

    @validator("departure_date")
    def validate_departure_date(cls, v):
        if v < date.today():
            raise ValueError("Departure date cannot be in the past.")
        return v

    @validator("arrival_date")
    def validate_arrival_date(cls, v, values):
        if "departure_date" in values and v < values["departure_date"]:
            raise ValueError("Arrival date must be after departure date.")
        return v

    @validator("arrival_time")
    def validate_arrival_time(cls, v, values):
        if "departure_date" in values and "arrival_date" in values and "departure_time" in values:
            if values["departure_date"] == values["arrival_date"] and v <= values["departure_time"]:
                raise ValueError("When departure and arrival are on the same date, arrival time must be after departure time.")
        return v
```

### 5. Schemas de Creación Completa

#### ActivityFullCreate
```python
class ActivityFullCreate(BaseModel):
    name: str
    description: str
    location_id: int
    date: date
    start_time: time
    duration_hours: int = Field(..., ge=1, le=24)
    include_guide: bool
    maximum_spaces: int = Field(..., ge=1, le=100)
    difficulty_level: Literal["Very Easy", "Easy", "Medium", "Hard", "Very Hard", "Extreme"]
    language: str
    available_slots: int = Field(..., ge=0, le=100)
    supplier_id: int
    precio_unitario: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=8)
    availabilities: List[ActivityAvailabilityCreateNested] = []

    @validator("date")
    def check_date(cls, v):
        if v < date.today():
            raise ValueError("La fecha de la actividad no puede estar en el pasado.")
        return v

    @validator("available_slots")
    def check_available_slots(cls, v, values):
        if "maximum_spaces" in values and v > values["maximum_spaces"]:
            raise ValueError("Los lugares disponibles no pueden exceder el máximo de espacios.")
        return v
```

#### LodgmentFullCreate
```python
class LodgmentFullCreate(BaseSchema):
    # Metadata
    precio_unitario: float = Field(..., gt=0)
    supplier_id: int

    # Alojamiento
    name: str = Field(..., max_length=128)
    description: Optional[str] = None
    location_id: int
    type: Literal["hotel", "hostel", "apartment", "house", "cabin", "resort", "bed_and_breakfast", "villa", "camping"]
    max_guests: int = Field(..., ge=1, le=50)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[EmailStr] = None
    amenities: List[str] = Field(default_factory=list)
    date_checkin: date
    date_checkout: date

    rooms: List[RoomCreateNested] = Field(default_factory=list)

    @validator("date_checkin")
    def validate_checkin_date(cls, v):
        if v < date.today():
            raise ValueError("La fecha de check-in no puede estar en el pasado.")
        return v

    @validator("date_checkout")
    def validate_checkout_date(cls, v, values):
        if "date_checkin" in values and v <= values["date_checkin"]:
            raise ValueError("La fecha de check-out debe ser posterior a la fecha de check-in.")
        return v
```

#### TransportationFullCreate
```python
class TransportationFullCreate(BaseModel):
    # Metadata
    precio_unitario: float = Field(..., gt=0)
    supplier_id: int

    # Transporte
    origin_id: int
    destination_id: int
    type: TransportationType = TransportationType.bus
    description: str
    notes: Optional[str] = ""
    capacity: int = Field(..., gt=0, le=100)

    # Disponibilidades
    availabilities: List[TransportationAvailabilityCreateNested] = Field(default_factory=list)

    @validator("description")
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError("La descripción es obligatoria")
        return v
``` 