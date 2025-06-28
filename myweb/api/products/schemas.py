from ninja import Schema
from typing import Union, Literal, Optional
from datetime import date, time, datetime
from pydantic import Field

class LocationOut(Schema):
    country: str
    state: str
    city: str

    class Config:
        from_attributes = True

# Actividad
class ActivityOut(Schema):
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

    class Config:
        from_attributes = True

# Vuelo
class FlightOut(Schema):
    id: int
    airline: str
    flight_number: str
    origin: LocationOut
    destination: LocationOut
    departure_date: date
    arrival_date: date
    duration_hours: int
    class_flight: str
    available_seats: int

    class Config:
        from_attributes = True

# Alojamiento
class LodgmentOut(Schema):
    id: int
    name: str
    location: LocationOut
    date_checkin: date
    date_checkout: date

    class Config:
        from_attributes = True

# Transporte
class TransportationOut(Schema):
    id: int
    origin: LocationOut
    destination: LocationOut
    departure_date: date
    arrival_date: date
    description: str
    capacity: int

    class Config:
        from_attributes = True

class ActivityCreate(Schema):
    name: str
    description: str
    location_id: int  # FK a Location
    date: date
    start_time: time
    duration_hours: int = Field(..., ge=0, le=24)
    include_guide: bool
    maximum_spaces: int = Field(..., ge=0)
    difficulty_level: Literal[
        "Very Easy", "Easy", "Medium", "Hard", "Very Hard", "Extreme"
    ]
    language: str
    available_slots: int = Field(..., ge=0)

class FlightCreate(Schema):
    airline: str
    flight_number: str
    origin_id: int       # FK a Location
    destination_id: int  # FK a Location
    departure_date: date
    arrival_date: date
    duration_hours: int = Field(..., ge=0, le=192)
    class_flight: Literal[
        "Basic Economy", "Economy", "Premium Economy", "Business Class", "First Class"
    ]
    available_seats: int = Field(..., ge=0)

class LodgmentCreate(Schema):
    name: str
    location_id: int
    date_checkin: date
    date_checkout: date

class TransportationCreate(Schema):
    origin_id: int
    destination_id: int
    departure_date: date
    arrival_date: date
    description: str
    capacity: int = Field(..., ge=0)

# Esquemas de actualización
class ActivityUpdate(Schema):
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

class FlightUpdate(Schema):
    airline: Optional[str] = None
    flight_number: Optional[str] = None
    origin_id: Optional[int] = None
    destination_id: Optional[int] = None
    departure_date: Optional[date] = None
    arrival_date: Optional[date] = None
    duration_hours: Optional[int] = Field(None, ge=0, le=192)
    class_flight: Optional[Literal[
        "Basic Economy", "Economy", "Premium Economy", "Business Class", "First Class"
    ]] = None
    available_seats: Optional[int] = Field(None, ge=0)

class LodgmentUpdate(Schema):
    name: Optional[str] = None
    location_id: Optional[int] = None
    date_checkin: Optional[date] = None
    date_checkout: Optional[date] = None

class TransportationUpdate(Schema):
    origin_id: Optional[int] = None
    destination_id: Optional[int] = None
    departure_date: Optional[date] = None
    arrival_date: Optional[date] = None
    description: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=0)

class ProductsMetadataOut(Schema):
    id: int
    precio_unitario: float
    tipo_producto: Literal["actividad", "vuelo", "alojamiento", "transporte"]
    producto: Union[ActivityOut, FlightOut, LodgmentOut, TransportationOut]

    class Config:
        from_attributes = True

class ProductsMetadataCreate(Schema):
    tipo_producto: Literal["actividad", "vuelo", "alojamiento", "transporte"]
    precio_unitario: float
    supplier_id: int  # clave foránea
    producto: Union[ActivityCreate, FlightCreate, LodgmentCreate, TransportationCreate]

class ProductsMetadataUpdate(Schema):
    precio_unitario: Optional[float] = None
    supplier_id:     Optional[int]   = None
    # tipo_producto **NO** se permite cambiar
    producto: Union[
        ActivityUpdate, FlightUpdate, LodgmentUpdate, TransportationUpdate, None
    ] = None