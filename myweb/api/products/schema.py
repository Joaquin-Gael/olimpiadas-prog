from ninja import Schema
from typing import Union, Literal
from datetime import date, time, datetime
from pydantic import Field

class LocationOut(Schema):
    country: str
    state: str
    city: str

    class Config:
        orm_mode = True

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
        orm_mode = True

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
        orm_mode = True

# Alojamiento
class LodgmentOut(Schema):
    id: int
    name: str
    location: LocationOut
    date_checkin: date
    date_checkout: date

    class Config:
        orm_mode = True

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
        orm_mode = True

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


class ProductsMetadataOut(Schema):
    id: int
    precio_unitario: float
    tipo_producto: Literal["actividad", "vuelo", "alojamiento", "transporte"]
    producto: Union[ActivityOut, FlightOut, LodgmentOut, TransportationOut]

    class Config:
        orm_mode = True

class ProductsMetadataCreate(Schema):
    tipo_producto: Literal["actividad", "vuelo", "alojamiento", "transporte"]
    precio_unitario: float
    supplier_id: int  # clave foránea
    producto: Union[ActivityCreate, FlightCreate, LodgmentCreate, TransportationCreate]
