from ninja import Schema
from pydantic import BaseModel, Field, field_validator, EmailStr, AnyUrl, ConfigDict
from typing import Union, Literal, Optional, List
from enum import Enum
from datetime import date, time, datetime
from api.products.common.schemas import BaseSchema


# ──────────────────────────────────────────────────────────────
# 1. BASE AND COMMON SCHEMAS
# ──────────────────────────────────────────────────────────────

class LocationOut(BaseSchema):
    """Schema for geographic locations"""
    country: str
    state: str
    city: str


# ──────────────────────────────────────────────────────────────
# 2. ACTIVITIES
# ──────────────────────────────────────────────────────────────

# Transportation
class TransportationOut(BaseSchema):
    id: int
    origin: LocationOut
    destination: LocationOut
    departure_date: date
    arrival_date: date
    description: str
    capacity: int

class ActivityCreate(BaseSchema):
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

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        if v < date.today():
            raise ValueError("Activity date cannot be in the past.")
        return v


class ActivityAvailabilityCreate(BaseSchema):
    """Schema to create activity availability"""
    event_date: date
    start_time: time
    total_seats: int = Field(..., ge=1, json_schema_extra={"description": "Total number of seats available"})
    reserved_seats: int = Field(..., ge=0, json_schema_extra={"description": "Number of already reserved seats"})
    price: float = Field(..., gt=0, json_schema_extra={"description": "Price per person"})
    currency: str = Field(..., max_length=8, json_schema_extra={"description": "Currency code, e.g., USD"})
    state: Optional[str] = Field(default="active")

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, v):
        if v < date.today():
            raise ValueError("Event date cannot be in the past.")
        return v

    @field_validator("reserved_seats")
    @classmethod
    def validate_reserved_seats(cls, v, info):
        values = info.data
        if "total_seats" in values and v > values["total_seats"]:
            raise ValueError("Reserved seats cannot exceed total seats.")
        return v


# ── UPDATE ────────────────────────────────────────────────────
class ActivityUpdate(Schema):
    """Schema to update an activity"""
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
    """Schema to update activity availability"""
    event_date: Optional[date] = None
    start_time: Optional[time] = None
    total_seats: Optional[int] = Field(None, ge=1)
    reserved_seats: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=8)
    state: Optional[str] = None


# ── OUTPUT ────────────────────────────────────────────────────
class ActivityOut(BaseSchema):
    """Output schema for activities"""
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
    """Output schema for activity availability"""
    id: int
    activity_id: int


# ──────────────────────────────────────────────────────────────
# 3. FLIGHTS
# ──────────────────────────────────────────────────────────────

# ── CREATE ────────────────────────────────────────────────────
class FlightCreate(BaseSchema):
    """Schema to create a flight"""
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
class FlightUpdate(Schema):
    """Schema to update a flight"""
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
    """Output schema for flights"""
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
    """Schema to create a lodging"""
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

    @field_validator("date_checkin")
    @classmethod
    def validate_checkin_date(cls, v):
        if v < date.today():
            raise ValueError("Check-in date cannot be in the past.")
        return v

    @field_validator("date_checkout")
    @classmethod
    def validate_checkout_date(cls, v, info):
        values = info.data
        if "date_checkin" in values and v <= values["date_checkin"]:
            raise ValueError("Check-out date must be after check-in date.")
        return v


class RoomCreate(BaseSchema):
    """Schema to create a room"""
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
    """Schema to create room availability"""
    room_id: int
    start_date: date
    end_date: date
    available_quantity: int = Field(..., ge=0)
    price_override: Optional[float] = Field(None, gt=0)
    currency: str = Field(default="USD", max_length=3)
    is_blocked: bool = False
    minimum_stay: int = Field(default=1, ge=1)

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v):
        if v < date.today():
            raise ValueError("Start date cannot be in the past.")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v, info):
        values = info.data
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date.")
        return v


# ── UPDATE ────────────────────────────────────────────────────
class LodgmentUpdate(Schema):
    """Schema to update a lodging"""
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
    """Schema to update a room"""
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
    """Schema to update room availability"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    available_quantity: Optional[int] = Field(None, ge=0)
    price_override: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    is_blocked: Optional[bool] = None
    minimum_stay: Optional[int] = Field(None, ge=1)


# ── OUTPUT ────────────────────────────────────────────────────
class LodgmentOut(BaseSchema):
    """Output schema for lodgings"""
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
    """Output schema for rooms"""
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
    """Output schema for room availability"""
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
    """Detailed output schema for lodgings with rooms"""
    rooms: List[RoomOut]


class RoomDetailOut(RoomOut):
    """Detailed output schema for rooms with availability"""
    availabilities: List[RoomAvailabilityOut]


class RoomWithAvailabilityOut(RoomOut):
    """Output schema for rooms with availability and effective price"""
    availabilities: List[RoomAvailabilityOut]
    effective_price: Optional[float] = None
    is_available_for_booking: bool = False


# ── SEARCH PARAMS ─────────────────────────────────────────────
class LodgmentSearchParams(BaseSchema):
    """Search parameters for lodgings"""
    location_id: Optional[int] = None
    type: Optional[str] = None
    checkin_date: Optional[date] = None
    checkout_date: Optional[date] = None
    guests: Optional[int] = Field(None, ge=1)
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    amenities: Optional[List[str]] = None


class RoomSearchParams(BaseSchema):
    """Search parameters for rooms"""
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
    """Available transportation types"""
    bus = "bus"
    van = "van"
    car = "car"
    shuttle = "shuttle"
    train = "train"
    other = "other"

# ── CREATE ────────────────────────────────────────────────────
class TransportationCreate(BaseSchema):
    """Schema to create transportation"""
    origin_id: int
    destination_id: int
    type: TransportationType = TransportationType.bus
    description: str
    notes: Optional[str] = ""
    capacity: int = Field(..., gt=0, le=100)

    @field_validator("description")
    @classmethod
    def desc_required(cls, v):
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v


class TransportationAvailabilityCreate(BaseSchema):
    """Schema to create transportation availability"""
    departure_date: date
    departure_time: time
    arrival_date: date
    arrival_time: time
    total_seats: int = Field(..., gt=0, description="Total number of seats available")
    reserved_seats: int = Field(..., ge=0, description="Number of already reserved seats")
    price: float = Field(..., gt=0, description="Price per person")
    currency: str = Field(..., max_length=8, description="Currency code, e.g., USD")
    state: Optional[str] = Field(default="active")

    @field_validator("departure_date")
    @classmethod
    def validate_departure_date(cls, v):
        if v < date.today():
            raise ValueError("Departure date cannot be in the past.")
        return v

    @field_validator("arrival_date")
    @classmethod
    def validate_arrival_date(cls, v, values):
        departure_date = values.get("departure_date")
        if departure_date and v < departure_date:
            raise ValueError("Arrival date cannot be before departure date.")
        return v

    @field_validator("arrival_time")
    @classmethod
    def validate_arrival_time(cls, v, values):
        departure_date = values.get("departure_date")
        arrival_date = values.get("arrival_date")
        departure_time = values.get("departure_time")

        if departure_date and arrival_date and departure_time:
            if departure_date == arrival_date and v <= departure_time:
                raise ValueError("Arrival time must be after departure time on the same day.")
        return v

    @field_validator("reserved_seats")
    @classmethod
    def validate_reserved_seats(cls, v, values):
        if "total_seats" in values and v > values["total_seats"]:
            raise ValueError("Reserved seats cannot exceed total seats.")
        return v


# ── UPDATE ────────────────────────────────────────────────────
class TransportationUpdate(Schema):
    """Schema to update transportation"""
    origin_id: Optional[int] = None
    destination_id: Optional[int] = None
    type: Optional[TransportationType] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    capacity: Optional[int] = Field(None, gt=0, le=100)
    is_active: Optional[bool] = None


class TransportationAvailabilityUpdate(BaseSchema):
    """Schema to update transportation availability"""
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
class TransportationOut(Schema):
    """Output schema for transportation"""
    id: int
    origin: LocationOut
    destination: LocationOut
    type: str
    description: str
    notes: Optional[str]
    capacity: int
    is_active: bool


class TransportationAvailabilityOut(TransportationAvailabilityCreate):
    """Output schema for transportation availability"""
    id: int
    transportation_id: int


# ──────────────────────────────────────────────────────────────
# 6. SUPPLIERS
# ──────────────────────────────────────────────────────────────

# ── CREATE ────────────────────────────────────────────────────
class SupplierCreate(BaseSchema):
    """Schema to create a supplier"""
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
    """Schema to update a supplier"""
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
    """Output schema for suppliers"""
    id: int
    name: str
    description: str
    street: str
    street_number: int
    city: str
    country: str
    email: str
    telephone: str
    website: str


# ──────────────────────────────────────────────────────────────
# 7. PRODUCT METADATA
# ──────────────────────────────────────────────────────────────

# ── OUTPUT ────────────────────────────────────────────────────
class ProductsMetadataOut(BaseSchema):
    """Output schema for product metadata"""
    id: int
    unit_price: float
    product_type: Literal["activity", "flight", "lodgment", "transportation"]
    product: Union[ActivityOut, FlightOut, LodgmentOut, TransportationOut]


class ProductsMetadataOutLodgmentDetail(BaseSchema):
    """Output schema for product metadata with lodging detail (includes rooms)"""
    id: int
    unit_price: float
    product_type: Literal["lodgment"]
    product: LodgmentDetailOut


# ── CREATE ────────────────────────────────────────────────────
class ProductsMetadataCreate(BaseSchema):
    """Schema to create product metadata"""
    product_type: Literal["activity", "flight", "lodgment", "transportation"]
    unit_price: float
    supplier_id: int
    product: Union[ActivityCreate, FlightCreate, LodgmentCreate, TransportationCreate]


# ── UPDATE ────────────────────────────────────────────────────
class ProductsMetadataUpdate(BaseSchema):
    """Base schema to update product metadata"""
    unit_price: Optional[float] = None
    supplier_id: Optional[int] = None
    product: Optional[Union[ActivityUpdate, FlightUpdate, LodgmentUpdate, TransportationUpdate]] = None


class ProductsMetadataUpdateActivity(ProductsMetadataUpdate):
    """Schema to update activity metadata"""
    product: Optional[ActivityUpdate] = None


class ProductsMetadataUpdateFlight(ProductsMetadataUpdate):
    """Schema to update flight metadata"""
    product: Optional[FlightUpdate] = None


class ProductsMetadataUpdateLodgment(ProductsMetadataUpdate):
    """Schema to update lodging metadata"""
    product: Optional[LodgmentUpdate] = None


class ProductsMetadataUpdateTransportation(ProductsMetadataUpdate):
    """Schema to update transportation metadata"""
    product: Optional[TransportationUpdate] = None


# ──────────────────────────────────────────────────────────────
# 6. SCHEMAS PARA CREACIÓN COMPLETA DE ACTIVIDADES
# ──────────────────────────────────────────────────────────────

class ActivityAvailabilityCreateNested(BaseSchema):
    """Schema for nested availability in complete activity creation"""
    event_date: date
    start_time: time
    total_seats: int = Field(..., ge=1)
    reserved_seats: int = Field(..., ge=0)
    price: float = Field(..., gt=0)
    currency: str = Field(..., max_length=8)

    @field_validator("event_date")
    @classmethod
    def check_event_date(cls, v):
        if v < date.today():
            raise ValueError("Date cannot be in the past.")
        return v

    @field_validator("reserved_seats")
    @classmethod
    def check_reserved_seats(cls, v, info):
        values = info.data
        total = values.get("total_seats", 0)
        if v > total:
            raise ValueError("Reserved seats cannot exceed total.")
        return v


class ActivityCompleteCreate(BaseSchema):
    """Schema to create a complete activity with availabilities"""
    # Activity data
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
    
    # Availabilities
    availabilities: List[ActivityAvailabilityCreateNested] = []

    @field_validator("date")
    @classmethod
    def check_date(cls, v):
        if v < date.today():
            raise ValueError("Activity date cannot be in the past.")
        return v


class ActivityMetadataCreate(BaseSchema):
    """Schema for activity metadata"""
    supplier_id: int
    unit_price: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=8)


# ──────────────────────────────────────────────────────────────
# 7. SCHEMAS FOR COMPLETE LODGING CREATION
# ──────────────────────────────────────────────────────────────

class RoomAvailabilityCreateNested(BaseSchema):
    """Schema for nested room availability in complete lodging creation"""
    start_date: date
    end_date: date
    available_quantity: int = Field(..., ge=0)
    price_override: Optional[float] = Field(None, gt=0)
    currency: str = Field(default="USD", max_length=3)
    is_blocked: bool = False
    minimum_stay: int = Field(default=1, ge=1)

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v):
        if v < date.today():
            raise ValueError("Start date cannot be in the past.")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v, info):
        values = info.data
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date.")
        return v


class RoomCreateNested(BaseSchema):
    """Schema for nested room in complete lodging creation"""
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


class LodgmentCompleteCreate(BaseSchema):
    """Schema to create a complete lodging with rooms and availabilities"""
    # Lodging data
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

    # Rooms
    rooms: List[RoomCreateNested] = Field(..., min_length=1)

    @field_validator("date_checkin")
    @classmethod
    def validate_checkin_date(cls, v):
        if v < date.today():
            raise ValueError("Check-in date cannot be in the past.")
        return v

    @field_validator("date_checkout")
    @classmethod
    def validate_checkout_date(cls, v, info):
        values = info.data
        if "date_checkin" in values and v <= values["date_checkin"]:
            raise ValueError("Check-out date must be after check-in date.")
        return v


class LodgmentMetadataCreate(BaseSchema):
    """Schema for lodging metadata"""
    supplier_id: int
    unit_price: float = Field(..., gt=0)


# ──────────────────────────────────────────────────────────────
# 8. SCHEMAS FOR COMPLETE TRANSPORTATION CREATION
# ──────────────────────────────────────────────────────────────

class TransportationAvailabilityCreateNested(BaseSchema):
    """Schema for nested transportation availability in complete creation"""
    departure_date: date
    departure_time: time
    arrival_date: date
    arrival_time: time
    total_seats: int = Field(..., gt=0)
    reserved_seats: int = Field(..., ge=0)
    price: float = Field(..., gt=0)
    currency: str = Field(..., max_length=8)
    state: str = Field(default="active")

    @field_validator("departure_date")
    @classmethod
    def check_departure_date(cls, v):
        if v < date.today():
            raise ValueError("Departure date cannot be in the past.")
        return v

    @field_validator("arrival_date")
    @classmethod
    def check_arrival_date(cls, v, info):
        values = info.data
        departure_date = values.get("departure_date")
        if departure_date and v < departure_date:
            raise ValueError("Arrival date cannot be before departure date.")
        return v

    @field_validator("arrival_time")
    @classmethod
    def check_arrival_time(cls, v, info):
        values = info.data
        departure_date = values.get("departure_date")
        arrival_date = values.get("arrival_date")
        departure_time = values.get("departure_time")

        if departure_date and arrival_date and departure_time:
            if departure_date == arrival_date and v <= departure_time:
                raise ValueError("Arrival time must be after departure time on the same day.")
        return v

    @field_validator("reserved_seats")
    @classmethod
    def check_reserved_seats(cls, v, info):
        values = info.data
        total = values.get("total_seats", 0)
        if v > total:
            raise ValueError("Reserved seats cannot exceed total.")
        return v


class TransportationCompleteCreate(BaseSchema):
    """Schema to create a complete transportation with availabilities"""
    # Transportation data
    origin_id: int
    destination_id: int
    type: TransportationType  # Required, no default value
    description: str
    notes: Optional[str] = ""
    capacity: int = Field(..., gt=0, le=100)

    # Availabilities
    availabilities: List[TransportationAvailabilityCreateNested] = Field(default_factory=list)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError("Description cannot be empty.")
        return v


class TransportationMetadataCreate(BaseSchema):
    """Schema for transportation metadata"""
    supplier_id: int
    unit_price: float = Field(..., gt=0)


# ──────────────────────────────────────────────────────────────
# 9. PACKAGES
# ──────────────────────────────────────────────────────────────

# ── CREATE ────────────────────────────────────────────────────
class ComponentPackageCreate(BaseSchema):
    """Schema to create a package component"""
    product_metadata_id: int
    order: int = Field(..., ge=0, json_schema_extra={"help_text": "Display order within the package"})
    quantity: Optional[int] = Field(None, ge=1, json_schema_extra={"help_text": "Number of times this product is included"})
    title: Optional[str] = Field(None, max_length=128, json_schema_extra={"help_text": "Visible name of the component"})
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v, info):
        values = info.data
        start = values.get("start_date")
        if v and not start:
            raise ValueError("Must set start_date if end_date is included.")
        if v and start and v < start:
            raise ValueError("End date cannot be earlier than start date.")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError("Quantity must be at least 1.")
        return v


class PackageCreate(BaseSchema):
    """Schema to create a package"""
    name: str = Field(..., max_length=64)
    description: str
    cover_image: Optional[str] = Field(None, max_length=500)
    
    # Prices
    base_price: Optional[float] = Field(None, ge=0)
    taxes: Optional[float] = Field(None, ge=0)
    final_price: float = Field(..., gt=0)
    
    # Package components
    components: List[ComponentPackageCreate] = Field(default_factory=list)

    @field_validator("final_price")
    @classmethod
    def validate_final_price(cls, v, info):
        values = info.data
        base_price = values.get("base_price")
        taxes = values.get("taxes")
        
        if base_price is not None and taxes is not None:
            total = round(base_price + taxes, 2)
            if round(v, 2) != total:
                raise ValueError("Final price does not match base + taxes.")
        return v


# ── UPDATE ────────────────────────────────────────────────────
class ComponentPackageUpdate(BaseSchema):
    """Schema to update a package component"""
    order: Optional[int] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=1)
    title: Optional[str] = Field(None, max_length=128)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v, info):
        values = info.data
        start = values.get("start_date")
        if v and not start:
            raise ValueError("Must set start_date if end_date is included.")
        if v and start and v < start:
            raise ValueError("End date cannot be earlier than start date.")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError("Quantity must be at least 1.")
        return v


class PackageUpdate(BaseSchema):
    """Schema to update a package"""
    name: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None
    cover_image: Optional[str] = None
    
    # Prices
    base_price: Optional[float] = Field(None, ge=0)
    taxes: Optional[float] = Field(None, ge=0)
    final_price: Optional[float] = Field(None, gt=0)
    
    is_active: Optional[bool] = None

    @field_validator("final_price")
    @classmethod
    def validate_final_price(cls, v, info):
        if v is not None:
            values = info.data
            base_price = values.get("base_price")
            taxes = values.get("taxes")
            
            if base_price is not None and taxes is not None:
                total = round(base_price + taxes, 2)
                if round(v, 2) != total:
                    raise ValueError("Final price does not match base + taxes.")
        return v


# ── OUTPUT ────────────────────────────────────────────────────
class ComponentPackageOut(BaseSchema):
    """Output schema for package components"""
    id: int
    product_metadata_id: int
    order: int
    quantity: Optional[int]
    title: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    
    # Related product information
    product_type: str
    product_name: str


class PackageOut(BaseSchema):
    """Output schema for packages"""
    id: int
    name: str
    description: str
    cover_image: Optional[str]
    
    # Prices
    base_price: Optional[float]
    taxes: Optional[float]
    final_price: float
    
    # Reviews
    rating_average: float
    total_reviews: int
    
    # Status
    is_active: bool
    
    # Dates
    created_at: datetime
    updated_at: datetime
    
    # Calculated duration
    duration_days: Optional[int]


class PackageDetailOut(PackageOut):
    """Detailed output schema for packages with components"""
    components: List[ComponentPackageOut]


# ── SEARCH PARAMS ─────────────────────────────────────────────
class PackageSearchParams(BaseSchema):
    """Search parameters for packages"""
    name: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    max_rating: Optional[float] = Field(None, ge=0, le=5)
    min_duration: Optional[int] = Field(None, ge=1)
    max_duration: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    product_type: Optional[str] = None  # activity, flight, lodgment, transportation


# ──────────────────────────────────────────────────────────────
# 10. SCHEMAS FOR COMPLETE PACKAGE CREATION
# ──────────────────────────────────────────────────────────────

class PackageCompleteCreate(BaseSchema):
    """Schema to create a complete package with all data"""
    # Package data
    name: str = Field(..., max_length=64)
    description: str
    cover_image: Optional[str] = Field(None, max_length=500)
    
    # Prices
    base_price: Optional[float] = Field(None, ge=0)
    taxes: Optional[float] = Field(None, ge=0)
    final_price: float = Field(..., gt=0)
    
    # Package components
    components: List[ComponentPackageCreate] = Field(default_factory=list)

    @field_validator("final_price")
    @classmethod
    def validate_final_price(cls, v, info):
        values = info.data
        base_price = values.get("base_price")
        taxes = values.get("taxes")
        
        if base_price is not None and taxes is not None:
            total = round(base_price + taxes, 2)
            if round(v, 2) != total:
                raise ValueError("Final price does not match base + taxes.")
        return v

    @field_validator("components")
    @classmethod
    def validate_components(cls, v):
        if not v:
            raise ValueError("Package must have at least one component.")
        
        # Validate that there are no duplicate orders
        orders = [comp.order for comp in v]
        if len(orders) != len(set(orders)):
            raise ValueError("Component orders must be unique.")
        
        return v


class CategoryCreate(BaseSchema):
    name: str = Field(..., max_length=64)
    description: Optional[str] = None
    icon: Optional[str] = None


class CategoryUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None
    icon: Optional[str] = None


class CategoryOut(BaseSchema):
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
