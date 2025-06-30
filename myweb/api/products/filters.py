# api/products/filters.py
from ninja import Schema
from typing import Literal, Optional, List
from datetime import date, time
from pydantic import Field, field_validator
from enum import Enum

# ──────────────────────────────────────────────────────────────
# ENUMERACIONES PARA FILTROS ESPECÍFICOS
# ──────────────────────────────────────────────────────────────

class DifficultyLevel(Enum):
    VERY_EASY = "Very Easy"
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    VERY_HARD = "Very Hard"
    EXTREME = "Extreme"

class FlightClass(Enum):
    BASIC_ECONOMY = "Basic Economy"
    ECONOMY = "Economy"
    PREMIUM_ECONOMY = "Premium Economy"
    BUSINESS = "Business Class"
    FIRST = "First Class"

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

class RoomType(Enum):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    QUADRUPLE = "quadruple"
    SUITE = "suite"
    FAMILY = "family"
    DORMITORY = "dormitory"
    STUDIO = "studio"

class SortOrder(Enum):
    PRICE_ASC = "unit_price"
    PRICE_DESC = "-unit_price"
    DATE_ASC = "date"
    DATE_DESC = "-date"
    NAME_ASC = "name"
    NAME_DESC = "-name"
    RATING_ASC = "rating"
    RATING_DESC = "-rating"
    POPULARITY_ASC = "popularity"
    POPULARITY_DESC = "-popularity"

# ──────────────────────────────────────────────────────────────
# FILTROS PRINCIPALES MEJORADOS
# ──────────────────────────────────────────────────────────────

class ProductosFiltro(Schema):
    # ──────────────────────────────────────────────────────────────
    # FILTROS BÁSICOS
    # ──────────────────────────────────────────────────────────────
    product_type: Optional[Literal["activity", "flight", "lodgment", "transportation"]] = None
    search: Optional[str] = Field(None, description="Búsqueda en nombre, descripción y otros campos")
    supplier_id: Optional[int] = Field(None, description="ID del proveedor")
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS DE UBICACIÓN
    # ──────────────────────────────────────────────────────────────
    destination_id: Optional[int] = Field(None, description="ID de la ubicación de destino")
    origin_id: Optional[int] = Field(None, description="ID de la ubicación de origen")
    location_id: Optional[int] = Field(None, description="ID de ubicación general (para actividades y alojamientos)")
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS DE FECHAS
    # ──────────────────────────────────────────────────────────────
    date_min: Optional[date] = Field(None, description="Fecha mínima para el producto")
    date_max: Optional[date] = Field(None, description="Fecha máxima para el producto")
    date_checkin: Optional[date] = Field(None, description="Fecha de check-in específica para alojamientos")
    date_checkout: Optional[date] = Field(None, description="Fecha de check-out específica para alojamientos")
    date_departure: Optional[date] = Field(None, description="Fecha de salida para vuelos y transporte")
    date_arrival: Optional[date] = Field(None, description="Fecha de llegada para vuelos y transporte")
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS DE PRECIO
    # ──────────────────────────────────────────────────────────────
    unit_price_min: Optional[float] = Field(None, ge=0, description="Precio mínimo")
    unit_price_max: Optional[float] = Field(None, ge=0, description="Precio máximo")
    price_per_night_min: Optional[float] = Field(None, ge=0, description="Precio mínimo por noche (alojamientos)")
    price_per_night_max: Optional[float] = Field(None, ge=0, description="Precio máximo por noche (alojamientos)")
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS DE DISPONIBILIDAD
    # ──────────────────────────────────────────────────────────────
    available_only: Optional[bool] = Field(True, description="Mostrar solo productos disponibles")
    capacity_min: Optional[int] = Field(None, ge=1, description="Capacidad mínima requerida")
    capacity_max: Optional[int] = Field(None, ge=1, description="Capacidad máxima")
    available_seats_min: Optional[int] = Field(None, ge=0, description="Asientos disponibles mínimos")
    available_seats_max: Optional[int] = Field(None, ge=0, description="Asientos disponibles máximos")
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS ESPECÍFICOS POR TIPO DE PRODUCTO
    # ──────────────────────────────────────────────────────────────
    
    # Actividades
    difficulty_level: Optional[Literal["Very Easy", "Easy", "Medium", "Hard", "Very Hard", "Extreme"]] = None
    include_guide: Optional[bool] = None
    language: Optional[str] = None
    duration_min: Optional[int] = Field(None, ge=0, le=24, description="Duración mínima en horas")
    duration_max: Optional[int] = Field(None, ge=0, le=24, description="Duración máxima en horas")
    
    # Vuelos
    airline: Optional[str] = None
    class_flight: Optional[Literal["Basic Economy", "Economy", "Premium Economy", "Business Class", "First Class"]] = None
    duration_flight_min: Optional[int] = Field(None, ge=0, description="Duración mínima del vuelo en horas")
    duration_flight_max: Optional[int] = Field(None, ge=0, description="Duración máxima del vuelo en horas")
    direct_flight: Optional[bool] = Field(None, description="Solo vuelos directos")
    
    # Alojamientos
    lodgment_type: Optional[Literal["hotel", "hostel", "apartment", "house", "cabin", "resort", "bed_and_breakfast", "villa", "camping"]] = None
    room_type: Optional[Literal["single", "double", "triple", "quadruple", "suite", "family", "dormitory", "studio"]] = None
    guests_min: Optional[int] = Field(None, ge=1, description="Número mínimo de huéspedes")
    guests_max: Optional[int] = Field(None, ge=1, description="Número máximo de huéspedes")
    nights_min: Optional[int] = Field(None, ge=1, description="Estadía mínima en noches")
    nights_max: Optional[int] = Field(None, ge=1, description="Estadía máxima en noches")
    amenities: Optional[List[str]] = Field(None, description="Lista de amenidades requeridas")
    
    # Características de habitación
    private_bathroom: Optional[bool] = None
    balcony: Optional[bool] = None
    air_conditioning: Optional[bool] = None
    wifi: Optional[bool] = None
    
    # Transporte
    transport_type: Optional[str] = None
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS DE ORDENAMIENTO Y PAGINACIÓN
    # ──────────────────────────────────────────────────────────────
    ordering: Optional[str] = Field(None, description="Campo de ordenamiento (ej: 'unit_price', '-unit_price', 'date', '-date')")
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS AVANZADOS
    # ──────────────────────────────────────────────────────────────
    rating_min: Optional[float] = Field(None, ge=0, le=5, description="Rating mínimo")
    rating_max: Optional[float] = Field(None, ge=0, le=5, description="Rating máximo")
    promotions_only: Optional[bool] = Field(False, description="Mostrar solo productos con promociones")
    last_minute: Optional[bool] = Field(False, description="Mostrar solo ofertas de última hora")
    featured_only: Optional[bool] = Field(False, description="Mostrar solo productos destacados")
    
    # ──────────────────────────────────────────────────────────────
    # VALIDACIONES
    # ──────────────────────────────────────────────────────────────
    
    @field_validator('unit_price_max')
    @classmethod
    def validate_unit_price_max(cls, v, info):
        values = info.data
        if v is not None and 'unit_price_min' in values and values['unit_price_min'] is not None:
            if v < values['unit_price_min']:
                raise ValueError('El precio máximo no puede ser menor que el precio mínimo')
        return v
    
    @field_validator('price_per_night_max')
    @classmethod
    def validate_price_per_night_max(cls, v, info):
        values = info.data
        if v is not None and 'price_per_night_min' in values and values['price_per_night_min'] is not None:
            if v < values['price_per_night_min']:
                raise ValueError('El precio máximo por noche no puede ser menor que el precio mínimo por noche')
        return v
    
    @field_validator('date_max')
    @classmethod
    def validate_date_max(cls, v, info):
        values = info.data
        if v is not None and 'date_min' in values and values['date_min'] is not None:
            if v < values['date_min']:
                raise ValueError('La fecha máxima no puede ser anterior a la fecha mínima')
        return v
    
    @field_validator('date_checkout')
    @classmethod
    def validate_date_checkout(cls, v, info):
        values = info.data
        if v is not None and 'date_checkin' in values and values['date_checkin'] is not None:
            if v <= values['date_checkin']:
                raise ValueError('La fecha de checkout debe ser posterior a la fecha de checkin')
        return v
    
    @field_validator('date_arrival')
    @classmethod
    def validate_date_arrival(cls, v, info):
        values = info.data
        if v is not None and 'date_departure' in values and values['date_departure'] is not None:
            if v < values['date_departure']:
                raise ValueError('La fecha de llegada no puede ser anterior a la fecha de salida')
        return v
    
    @field_validator('capacity_max')
    @classmethod
    def validate_capacity_max(cls, v, info):
        values = info.data
        if v is not None and 'capacity_min' in values and values['capacity_min'] is not None:
            if v < values['capacity_min']:
                raise ValueError('La capacidad máxima no puede ser menor que la capacidad mínima')
        return v
    
    @field_validator('available_seats_max')
    @classmethod
    def validate_available_seats_max(cls, v, info):
        values = info.data
        if v is not None and 'available_seats_min' in values and values['available_seats_min'] is not None:
            if v < values['available_seats_min']:
                raise ValueError('Los asientos disponibles máximos no pueden ser menores que los mínimos')
        return v
    
    @field_validator('duration_max')
    @classmethod
    def validate_duration_max(cls, v, info):
        values = info.data
        if v is not None and 'duration_min' in values and values['duration_min'] is not None:
            if v < values['duration_min']:
                raise ValueError('La duración máxima no puede ser menor que la duración mínima')
        return v
    
    @field_validator('duration_flight_max')
    @classmethod
    def validate_duration_flight_max(cls, v, info):
        values = info.data
        if v is not None and 'duration_flight_min' in values and values['duration_flight_min'] is not None:
            if v < values['duration_flight_min']:
                raise ValueError('La duración máxima del vuelo no puede ser menor que la mínima')
        return v
    
    @field_validator('guests_max')
    @classmethod
    def validate_guests_max(cls, v, info):
        values = info.data
        if v is not None and 'guests_min' in values and values['guests_min'] is not None:
            if v < values['guests_min']:
                raise ValueError('El número máximo de huéspedes no puede ser menor que el mínimo')
        return v
    
    @field_validator('nights_max')
    @classmethod
    def validate_nights_max(cls, v, info):
        values = info.data
        if v is not None and 'nights_min' in values and values['nights_min'] is not None:
            if v < values['nights_min']:
                raise ValueError('La estadía máxima no puede ser menor que la mínima')
        return v
    
    @field_validator('rating_max')
    @classmethod
    def validate_rating_max(cls, v, info):
        values = info.data
        if v is not None and 'rating_min' in values and values['rating_min'] is not None:
            if v < values['rating_min']:
                raise ValueError('El rating máximo no puede ser menor que el mínimo')
        return v

# ──────────────────────────────────────────────────────────────
# FILTROS ESPECÍFICOS POR TIPO DE PRODUCTO
# ──────────────────────────────────────────────────────────────

class ActivityFilter(Schema):
    """Filtros específicos para actividades"""
    difficulty_level: Optional[Literal["Very Easy", "Easy", "Medium", "Hard", "Very Hard", "Extreme"]] = None
    include_guide: Optional[bool] = None
    language: Optional[str] = None
    duration_min: Optional[int] = Field(None, ge=0, le=24)
    duration_max: Optional[int] = Field(None, ge=0, le=24)
    specific_date: Optional[date] = None
    start_time: Optional[time] = None

class FlightFilter(Schema):
    """Filtros específicos para vuelos"""
    airline: Optional[str] = None
    class_flight: Optional[Literal["Basic Economy", "Economy", "Premium Economy", "Business Class", "First Class"]] = None
    duration_flight_min: Optional[int] = Field(None, ge=0)
    duration_flight_max: Optional[int] = Field(None, ge=0)
    direct_flight: Optional[bool] = None
    terminal: Optional[str] = None

class LodgmentFilter(Schema):
    """Filtros específicos para alojamientos"""
    lodgment_type: Optional[Literal["hotel", "hostel", "apartment", "house", "cabin", "resort", "bed_and_breakfast", "villa", "camping"]] = None
    room_type: Optional[Literal["single", "double", "triple", "quadruple", "suite", "family", "dormitory", "studio"]] = None
    guests_min: Optional[int] = Field(None, ge=1)
    guests_max: Optional[int] = Field(None, ge=1)
    nights_min: Optional[int] = Field(None, ge=1)
    amenities: Optional[List[str]] = None
    private_bathroom: Optional[bool] = None
    balcony: Optional[bool] = None
    air_conditioning: Optional[bool] = None
    wifi: Optional[bool] = None

class TransportationFilter(Schema):
    """Filtros específicos para transporte"""
    transport_type: Optional[str] = None
    trip_duration_min: Optional[int] = Field(None, ge=0)
    trip_duration_max: Optional[int] = Field(None, ge=0)

# ──────────────────────────────────────────────────────────────
# FILTROS ESPECIALIZADOS
# ──────────────────────────────────────────────────────────────

class AvailabilityFilter(Schema):
    """Filtros específicos para disponibilidad"""
    start_date: date
    end_date: date
    people_count: Optional[int] = Field(1, ge=1)
    rooms_count: Optional[int] = Field(1, ge=1)
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        values = info.data
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v

class AdvancedSearchFilter(Schema):
    """Filtros para búsqueda avanzada con múltiples criterios"""
    terms: List[str] = Field(..., description="Lista de términos de búsqueda")
    fields: Optional[List[str]] = Field(None, description="Campos específicos donde buscar")
    operator: Optional[Literal["AND", "OR"]] = Field("OR", description="Operador lógico para combinar términos")
    fuzzy: Optional[bool] = Field(False, description="Búsqueda aproximada")
    
    @field_validator('fields')
    @classmethod
    def validate_fields(cls, v):
        if v is not None:
            valid_fields = ['name', 'description', 'airline', 'flight_number', 'location']
            invalid_fields = [field for field in v if field not in valid_fields]
            if invalid_fields:
                raise ValueError(f'Campos inválidos: {invalid_fields}. Campos válidos: {valid_fields}')
        return v 