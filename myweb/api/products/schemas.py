from ninja import Schema
from pydantic import BaseModel, Field, validator, EmailStr, AnyUrl
from typing import Union, Literal, Optional, List
from enum import Enum
from datetime import date, time, datetime
from api.products.common.schemas import BaseSchema


# ──────────────────────────────────────────────────────────────
# 1. SCHEMAS BASE Y COMUNES
# ──────────────────────────────────────────────────────────────

class LocationOut(BaseSchema):
    """Schema para ubicaciones geográficas"""
    country: str
    state: str
    city: str


# ──────────────────────────────────────────────────────────────
# 2. ACTIVIDADES (ACTIVITIES)
# ──────────────────────────────────────────────────────────────

# ── CREATE ────────────────────────────────────────────────────
class ActivityCreate(BaseSchema):
    """Schema para crear una actividad"""
    name: str
    description: str
    location_id: int
    date: date
    start_time: time
    duration_hours: int = Field(..., ge=0, le=24)
    include_guide: bool
    maximum_spaces: int = Field(..., ge=0, le=100)
    difficulty_level: Literal[
        "Very Easy", "Easy", "Medium", "Hard", "Very Hard", "Extreme"
    ]
    language: str
    available_slots: int = Field(..., ge=0, le=100)

    @validator("date")
    def validate_date(cls, v):
        if v < date.today():
            raise ValueError("La fecha de la actividad no puede estar en el pasado.")
        return v


class ActivityAvailabilityCreate(BaseModel):
    """Schema para crear disponibilidad de actividad"""
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


# ── UPDATE ────────────────────────────────────────────────────
class ActivityUpdate(BaseSchema):
    """Schema para actualizar una actividad"""
    name: Optional[str] = None
    description: Optional[str] = None
    location_id: Optional[int] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    duration_hours: Optional[int] = Field(None, ge=0, le=24)
    include_guide: Optional[bool] = None
    maximum_spaces: Optional[int] = Field(None, ge=0)
    difficulty_level: Optional[Literal[
        "Very Easy", "Easy", "Medium", "Hard", "Very Hard", "Extreme"
    ]] = None
    language: Optional[str] = None
    available_slots: Optional[int] = Field(None, ge=0)


class ActivityAvailabilityUpdate(BaseSchema):
    """Schema para actualizar disponibilidad de actividad"""
    event_date: Optional[date] = None
    start_time: Optional[time] = None
    total_seats: Optional[int] = Field(None, ge=1)
    reserved_seats: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=8)
    state: Optional[str] = None


# ── OUTPUT ────────────────────────────────────────────────────
class ActivityOut(BaseSchema):
    """Schema de salida para actividades"""
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


class ActivityAvailabilityOut(ActivityAvailabilityCreate):
    """Schema de salida para disponibilidad de actividades"""
    id: int
    activity_id: int

    class Config:
        orm_mode = True


# ──────────────────────────────────────────────────────────────
# 3. VUELOS (FLIGHTS)
# ──────────────────────────────────────────────────────────────

# ── CREATE ────────────────────────────────────────────────────
class FlightCreate(BaseSchema):
    """Schema para crear un vuelo"""
    airline: str
    flight_number: str
    origin_id: int
    destination_id: int
    departure_date: date
    departure_time: time
    arrival_date: date
    arrival_time: time
    duration_hours: int = Field(..., ge=0, le=192)
    class_flight: Literal[
        "Basic Economy", "Economy", "Premium Economy", "Business Class", "First Class"
    ]
    available_seats: int = Field(..., ge=0, le=500)
    luggage_info: str
    aircraft_type: str
    terminal: Optional[str] = None
    gate: Optional[str] = None
    notes: Optional[str] = None


# ── UPDATE ────────────────────────────────────────────────────
class FlightUpdate(BaseSchema):
    """Schema para actualizar un vuelo"""
    airline: Optional[str] = None
    flight_number: Optional[str] = None
    origin_id: Optional[int] = None
    destination_id: Optional[int] = None
    departure_date: Optional[date] = None
    departure_time: Optional[time] = None
    arrival_date: Optional[date] = None
    arrival_time: Optional[time] = None
    duration_hours: Optional[int] = Field(None, ge=0, le=192)
    class_flight: Optional[Literal[
        "Basic Economy", "Economy", "Premium Economy", "Business Class", "First Class"
    ]] = None
    available_seats: Optional[int] = Field(None, ge=0, le=500)
    luggage_info: Optional[str] = None
    aircraft_type: Optional[str] = None
    terminal: Optional[str] = None
    gate: Optional[str] = None
    notes: Optional[str] = None


# ── OUTPUT ────────────────────────────────────────────────────
class FlightOut(BaseSchema):
    """Schema de salida para vuelos"""
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


# ──────────────────────────────────────────────────────────────
# 4. ALOJAMIENTOS (LODGMENTS)
# ──────────────────────────────────────────────────────────────

# ── CREATE ────────────────────────────────────────────────────
class LodgmentCreate(BaseSchema):
    """Schema para crear un alojamiento"""
    name: str = Field(..., max_length=128)
    description: Optional[str] = None
    location_id: int
    type: Literal[
        "hotel", "hostel", "apartment", "house", "cabin", 
        "resort", "bed_and_breakfast", "villa", "camping"
    ]
    max_guests: int = Field(..., ge=1, le=50)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[EmailStr] = None
    amenities: List[str] = Field(default_factory=list)
    date_checkin: date
    date_checkout: date

    @validator("date_checkin")
    def validate_checkin_date(cls, v):
        if v < date.today():
            raise ValueError("Check-in date cannot be in the past.")
        return v

    @validator("date_checkout")
    def validate_checkout_date(cls, v, values):
        if "date_checkin" in values and v <= values["date_checkin"]:
            raise ValueError("Check-out date must be after check-in date.")
        return v


class RoomCreate(BaseSchema):
    """Schema para crear una habitación"""
    lodgment_id: int
    room_type: Literal[
        "single", "double", "triple", "quadruple", 
        "suite", "family", "dormitory", "studio"
    ]
    name: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None
    capacity: int = Field(..., ge=1, le=20)
    has_private_bathroom: bool = True
    has_balcony: bool = False
    has_air_conditioning: bool = True
    has_wifi: bool = True
    base_price_per_night: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)


class RoomAvailabilityCreate(BaseSchema):
    """Schema para crear disponibilidad de habitación"""
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


# ── UPDATE ────────────────────────────────────────────────────
class LodgmentUpdate(BaseSchema):
    """Schema para actualizar un alojamiento"""
    name: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = None
    location_id: Optional[int] = None
    type: Optional[Literal[
        "hotel", "hostel", "apartment", "house", "cabin", 
        "resort", "bed_and_breakfast", "villa", "camping"
    ]] = None
    max_guests: Optional[int] = Field(None, ge=1, le=50)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[EmailStr] = None
    amenities: Optional[List[str]] = None
    date_checkin: Optional[date] = None
    date_checkout: Optional[date] = None
    is_active: Optional[bool] = None


class RoomUpdate(BaseSchema):
    """Schema para actualizar una habitación"""
    room_type: Optional[Literal[
        "single", "double", "triple", "quadruple", 
        "suite", "family", "dormitory", "studio"
    ]] = None
    name: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=1, le=20)
    has_private_bathroom: Optional[bool] = None
    has_balcony: Optional[bool] = None
    has_air_conditioning: Optional[bool] = None
    has_wifi: Optional[bool] = None
    base_price_per_night: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    is_active: Optional[bool] = None


class RoomAvailabilityUpdate(BaseSchema):
    """Schema para actualizar disponibilidad de habitación"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    available_quantity: Optional[int] = Field(None, ge=0)
    price_override: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    is_blocked: Optional[bool] = None
    minimum_stay: Optional[int] = Field(None, ge=1)


# ── OUTPUT ────────────────────────────────────────────────────
class LodgmentOut(BaseSchema):
    """Schema de salida para alojamientos"""
    id: int
    name: str
    description: Optional[str]
    location: LocationOut
    type: str
    max_guests: int
    contact_phone: Optional[str]
    contact_email: Optional[str]
    amenities: List[str]
    date_checkin: date
    date_checkout: date
    created_at: datetime
    updated_at: datetime
    is_active: bool


class RoomOut(BaseSchema):
    """Schema de salida para habitaciones"""
    id: int
    lodgment_id: int
    room_type: str
    name: Optional[str]
    description: Optional[str]
    capacity: int
    has_private_bathroom: bool
    has_balcony: bool
    has_air_conditioning: bool
    has_wifi: bool
    base_price_per_night: float
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RoomAvailabilityOut(BaseSchema):
    """Schema de salida para disponibilidad de habitaciones"""
    id: int
    room_id: int
    start_date: date
    end_date: date
    available_quantity: int
    price_override: Optional[float]
    currency: str
    is_blocked: bool
    minimum_stay: int
    created_at: datetime
    updated_at: datetime


# ── DETAILED OUTPUT ───────────────────────────────────────────
class LodgmentDetailOut(LodgmentOut):
    """Schema de salida detallado para alojamientos con habitaciones"""
    rooms: List[RoomOut]


class RoomDetailOut(RoomOut):
    """Schema de salida detallado para habitaciones con disponibilidad"""
    availabilities: List[RoomAvailabilityOut]


class LodgmentWithRoomsOut(LodgmentOut):
    """Schema de salida para alojamientos con habitaciones"""
    rooms: List[RoomOut]


class RoomWithAvailabilityOut(RoomOut):
    """Schema de salida para habitaciones con disponibilidad y precio efectivo"""
    availabilities: List[RoomAvailabilityOut]
    effective_price: Optional[float] = None
    is_available_for_booking: bool = False


# ── SEARCH PARAMS ─────────────────────────────────────────────
class LodgmentSearchParams(BaseSchema):
    """Parámetros de búsqueda para alojamientos"""
    location_id: Optional[int] = None
    type: Optional[str] = None
    checkin_date: Optional[date] = None
    checkout_date: Optional[date] = None
    guests: Optional[int] = Field(None, ge=1)
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    amenities: Optional[List[str]] = None


class RoomSearchParams(BaseSchema):
    """Parámetros de búsqueda para habitaciones"""
    lodgment_id: Optional[int] = None
    room_type: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    has_private_bathroom: Optional[bool] = None
    has_balcony: Optional[bool] = None
    has_air_conditioning: Optional[bool] = None
    has_wifi: Optional[bool] = None


# ──────────────────────────────────────────────────────────────
# 5. TRANSPORTE (TRANSPORTATION)
# ──────────────────────────────────────────────────────────────

# ── ENUM ─────────────────────────────────────────────────────
class TransportationType(str, Enum):
    """Tipos de transporte disponibles"""
    bus = "bus"
    van = "van"
    car = "car"
    shuttle = "shuttle"
    train = "train"
    other = "other"

# ── CREATE ────────────────────────────────────────────────────
class TransportationCreate(BaseSchema):
    """Schema para crear transporte"""
    origin_id: int
    destination_id: int
    type: TransportationType = TransportationType.bus
    description: str
    notes: Optional[str] = ""
    capacity: int = Field(..., gt=0, le=100)

    @validator("description")
    def desc_required(cls, v):
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v


class TransportationAvailabilityCreate(BaseModel):
    """Schema para crear disponibilidad de transporte"""
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
        departure_date = values.get("departure_date")
        if departure_date and v < departure_date:
            raise ValueError("Arrival date cannot be before departure date.")
        return v

    @validator("arrival_time")
    def validate_arrival_time(cls, v, values):
        departure_date = values.get("departure_date")
        arrival_date = values.get("arrival_date")
        departure_time = values.get("departure_time")
        
        if departure_date and arrival_date and departure_time:
            if departure_date == arrival_date and v <= departure_time:
                raise ValueError("Arrival time must be after departure time on the same day.")
        return v

    @validator("reserved_seats")
    def validate_reserved_seats(cls, v, values):
        if "total_seats" in values and v > values["total_seats"]:
            raise ValueError("Reserved seats cannot exceed total seats.")
        return v


# ── UPDATE ────────────────────────────────────────────────────
class TransportationUpdate(BaseSchema):
    """Schema para actualizar transporte"""
    origin_id: Optional[int] = None
    destination_id: Optional[int] = None
    type: Optional[TransportationType] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    capacity: Optional[int] = Field(None, gt=0, le=100)
    is_active: Optional[bool] = None


class TransportationAvailabilityUpdate(BaseSchema):
    """Schema para actualizar disponibilidad de transporte"""
    departure_date: Optional[date] = None
    departure_time: Optional[time] = None
    arrival_date: Optional[date] = None
    arrival_time: Optional[time] = None
    total_seats: Optional[int] = Field(None, gt=0)
    reserved_seats: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=8)
    state: Optional[str] = None


# ── OUTPUT ────────────────────────────────────────────────────
class TransportationOut(BaseSchema):
    """Schema de salida para transporte"""
    id: int
    origin: LocationOut
    destination: LocationOut
    type: str
    description: str
    notes: Optional[str]
    capacity: int
    is_active: bool


class TransportationAvailabilityOut(TransportationAvailabilityCreate):
    """Schema de salida para disponibilidad de transporte"""
    id: int
    transportation_id: int

    class Config:
        orm_mode = True


# ──────────────────────────────────────────────────────────────
# 6. PROVEEDORES (SUPPLIERS)
# ──────────────────────────────────────────────────────────────

# ── CREATE ────────────────────────────────────────────────────
class SupplierCreate(BaseSchema):
    """Schema para crear un proveedor"""
    first_name: str
    last_name: str
    organization_name: str
    description: str
    street: str
    street_number: int
    city: str
    country: str
    email: EmailStr
    telephone: str
    website: str


# ── UPDATE ────────────────────────────────────────────────────
class SupplierUpdate(BaseSchema):
    """Schema para actualizar un proveedor"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_name: Optional[str] = None
    description: Optional[str] = None
    street: Optional[str] = None
    street_number: Optional[int] = None
    city: Optional[str] = None
    country: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    website: Optional[AnyUrl] = None


# ── OUTPUT ────────────────────────────────────────────────────
class SupplierOut(BaseSchema):
    """Schema de salida para proveedores"""
    id: int
    first_name: str
    last_name: str
    organization_name: str
    description: str
    street: str
    street_number: int
    city: str
    country: str
    email: str
    telephone: str
    website: str


# ──────────────────────────────────────────────────────────────
# 7. METADATA DE PRODUCTOS
# ──────────────────────────────────────────────────────────────

# ── OUTPUT ────────────────────────────────────────────────────
class ProductsMetadataOut(BaseSchema):
    """Schema de salida para metadata de productos"""
    id: int
    precio_unitario: float
    tipo_producto: Literal["activity", "flight", "lodgment", "transportation"]
    producto: Union[ActivityOut, FlightOut, LodgmentOut, TransportationOut]


# ── CREATE ────────────────────────────────────────────────────
class ProductsMetadataCreate(BaseSchema):
    """Schema para crear metadata de productos"""
    tipo_producto: Literal["activity", "flight", "lodgment", "transportation"]
    precio_unitario: float
    supplier_id: int
    producto: Union[ActivityCreate, FlightCreate, LodgmentCreate, TransportationCreate]


# ── UPDATE ────────────────────────────────────────────────────
class ProductsMetadataUpdate(BaseSchema):
    """Schema base para actualizar metadata de productos"""
    precio_unitario: Optional[float] = None
    supplier_id: Optional[int] = None
    producto: Optional[Union[ActivityUpdate, FlightUpdate, LodgmentUpdate, TransportationUpdate]] = None


class ProductsMetadataUpdateActivity(ProductsMetadataUpdate):
    """Schema para actualizar metadata de actividades"""
    producto: Optional[ActivityUpdate] = None


class ProductsMetadataUpdateFlight(ProductsMetadataUpdate):
    """Schema para actualizar metadata de vuelos"""
    producto: Optional[FlightUpdate] = None


class ProductsMetadataUpdateLodgment(ProductsMetadataUpdate):
    """Schema para actualizar metadata de alojamientos"""
    producto: Optional[LodgmentUpdate] = None


class ProductsMetadataUpdateTransportation(ProductsMetadataUpdate):
    """Schema para actualizar metadata de transporte"""
    producto: Optional[TransportationUpdate] = None


# ──────────────────────────────────────────────────────────────
# 6. SCHEMAS PARA CREACIÓN COMPLETA DE ACTIVIDADES
# ──────────────────────────────────────────────────────────────

class ActivityAvailabilityCreateNested(BaseModel):
    """Schema para disponibilidad anidada en creación completa de actividad"""
    event_date: date
    start_time: time
    total_seats: int = Field(..., ge=1)
    reserved_seats: int = Field(..., ge=0)
    price: float = Field(..., gt=0)
    currency: str = Field(..., max_length=8)

    @validator("event_date")
    def check_event_date(cls, v):
        if v < date.today():
            raise ValueError("La fecha no puede estar en el pasado.")
        return v

    @validator("reserved_seats")
    def check_reserved_seats(cls, v, values):
        total = values.get("total_seats", 0)
        if v > total:
            raise ValueError("Los lugares reservados no pueden superar el total.")
        return v


class ActivityFullCreate(BaseModel):
    """Schema para crear una actividad completa con disponibilidades"""
    name: str
    description: str
    location_id: int
    date: date
    start_time: time
    duration_hours: int = Field(..., ge=1, le=24)
    include_guide: bool
    maximum_spaces: int = Field(..., ge=1, le=100)
    difficulty_level: Literal[
        "Very Easy", "Easy", "Medium", "Hard", "Very Hard", "Extreme"
    ]
    language: str
    available_slots: int = Field(..., ge=0, le=100)
    supplier_id: int
    precio_unitario: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=8)
    availabilities: List[ActivityAvailabilityCreateNested] = []

    @validator("date")
    def check_date(cls, v):
        if v < date.today():
            raise ValueError("La fecha de la actividad no puede ser en el pasado.")
        return v


# ──────────────────────────────────────────────────────────────
# 7. SCHEMAS PARA CREACIÓN COMPLETA DE ALOJAMIENTOS
# ──────────────────────────────────────────────────────────────

class RoomAvailabilityCreateNested(BaseSchema):
    """Schema para disponibilidad de habitación anidada en creación completa de alojamiento"""
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


class RoomCreateNested(BaseSchema):
    """Schema para habitación anidada en creación completa de alojamiento"""
    room_type: Literal[
        "single", "double", "triple", "quadruple", 
        "suite", "family", "dormitory", "studio"
    ]
    name: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None
    capacity: int = Field(..., ge=1, le=20)
    has_private_bathroom: bool = True
    has_balcony: bool = False
    has_air_conditioning: bool = True
    has_wifi: bool = True
    base_price_per_night: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)

    availabilities: List[RoomAvailabilityCreateNested] = Field(default_factory=list)


class LodgmentFullCreate(BaseSchema):
    """Schema para crear un alojamiento completo con habitaciones y disponibilidades"""
    # Metadata
    precio_unitario: float = Field(..., gt=0)
    supplier_id: int

    # Alojamiento
    name: str = Field(..., max_length=128)
    description: Optional[str] = None
    location_id: int
    type: Literal[
        "hotel", "hostel", "apartment", "house", "cabin", 
        "resort", "bed_and_breakfast", "villa", "camping"
    ]
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
            raise ValueError("Check-in date cannot be in the past.")
        return v

    @validator("date_checkout")
    def validate_checkout_date(cls, v, values):
        if "date_checkin" in values and v <= values["date_checkin"]:
            raise ValueError("Check-out date must be after check-in date.")
        return v


# ──────────────────────────────────────────────────────────────
# 8. SCHEMAS PARA CREACIÓN COMPLETA DE TRANSPORTE
# ──────────────────────────────────────────────────────────────

class TransportationAvailabilityCreateNested(BaseModel):
    """Schema para disponibilidad de transporte anidada en creación completa"""
    departure_date: date
    departure_time: time
    arrival_date: date
    arrival_time: time
    total_seats: int = Field(..., gt=0)
    reserved_seats: int = Field(..., ge=0)
    price: float = Field(..., gt=0)
    currency: str = Field(..., max_length=8)
    state: str = Field(default="active")

    @validator("departure_date")
    def check_departure_date(cls, v):
        if v < date.today():
            raise ValueError("La fecha de salida no puede estar en el pasado.")
        return v

    @validator("arrival_date")
    def check_arrival_date(cls, v, values):
        departure_date = values.get("departure_date")
        if departure_date and v < departure_date:
            raise ValueError("La fecha de llegada no puede ser anterior a la de salida.")
        return v

    @validator("arrival_time")
    def check_arrival_time(cls, v, values):
        departure_date = values.get("departure_date")
        arrival_date = values.get("arrival_date")
        departure_time = values.get("departure_time")
        
        if departure_date and arrival_date and departure_time:
            if departure_date == arrival_date and v <= departure_time:
                raise ValueError("La hora de llegada debe ser posterior a la de salida en el mismo día.")
        return v

    @validator("reserved_seats")
    def check_reserved_seats(cls, v, values):
        total = values.get("total_seats", 0)
        if v > total:
            raise ValueError("Los asientos reservados no pueden superar el total.")
        return v


class TransportationFullCreate(BaseModel):
    """Schema para crear un transporte completo con disponibilidades"""
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
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía.")
        return v
