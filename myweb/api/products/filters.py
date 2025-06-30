# api/products/filters.py
from ninja import Schema
from typing import Literal, Optional, List
from datetime import date, time
from pydantic import Field, validator
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
    PRICE_ASC = "precio"
    PRICE_DESC = "-precio"
    DATE_ASC = "fecha"
    DATE_DESC = "-fecha"
    NAME_ASC = "nombre"
    NAME_DESC = "-nombre"
    RATING_ASC = "rating"
    RATING_DESC = "-rating"
    POPULARITY_ASC = "popularidad"
    POPULARITY_DESC = "-popularidad"

# ──────────────────────────────────────────────────────────────
# FILTROS PRINCIPALES MEJORADOS
# ──────────────────────────────────────────────────────────────

class ProductosFiltro(Schema):
    # ──────────────────────────────────────────────────────────────
    # FILTROS BÁSICOS
    # ──────────────────────────────────────────────────────────────
    tipo: Optional[Literal["activity", "flight", "lodgment", "transportation"]] = None
    search: Optional[str] = Field(None, description="Búsqueda en nombre, descripción y otros campos")
    supplier_id: Optional[int] = Field(None, description="ID del proveedor")
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS DE UBICACIÓN
    # ──────────────────────────────────────────────────────────────
    destino_id: Optional[int] = Field(None, description="ID de la ubicación de destino")
    origen_id: Optional[int] = Field(None, description="ID de la ubicación de origen")
    location_id: Optional[int] = Field(None, description="ID de ubicación general (para actividades y alojamientos)")
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS DE FECHAS
    # ──────────────────────────────────────────────────────────────
    fecha_min: Optional[date] = Field(None, description="Fecha mínima para el producto")
    fecha_max: Optional[date] = Field(None, description="Fecha máxima para el producto")
    fecha_checkin: Optional[date] = Field(None, description="Fecha de check-in específica para alojamientos")
    fecha_checkout: Optional[date] = Field(None, description="Fecha de check-out específica para alojamientos")
    fecha_salida: Optional[date] = Field(None, description="Fecha de salida para vuelos y transporte")
    fecha_llegada: Optional[date] = Field(None, description="Fecha de llegada para vuelos y transporte")
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS DE PRECIO
    # ──────────────────────────────────────────────────────────────
    precio_min: Optional[float] = Field(None, ge=0, description="Precio mínimo")
    precio_max: Optional[float] = Field(None, ge=0, description="Precio máximo")
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS DE DISPONIBILIDAD
    # ──────────────────────────────────────────────────────────────
    disponibles_solo: Optional[bool] = Field(True, description="Mostrar solo productos disponibles")
    capacidad_min: Optional[int] = Field(None, ge=1, description="Capacidad mínima requerida")
    capacidad_max: Optional[int] = Field(None, ge=1, description="Capacidad máxima")
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS ESPECÍFICOS POR TIPO DE PRODUCTO
    # ──────────────────────────────────────────────────────────────
    
    # Actividades
    nivel_dificultad: Optional[Literal["Very Easy", "Easy", "Medium", "Hard", "Very Hard", "Extreme"]] = None
    incluye_guia: Optional[bool] = None
    idioma: Optional[str] = None
    duracion_min: Optional[int] = Field(None, ge=0, le=24, description="Duración mínima en horas")
    duracion_max: Optional[int] = Field(None, ge=0, le=24, description="Duración máxima en horas")
    
    # Vuelos
    aerolinea: Optional[str] = None
    clase_vuelo: Optional[Literal["Basic Economy", "Economy", "Premium Economy", "Business Class", "First Class"]] = None
    duracion_vuelo_min: Optional[int] = Field(None, ge=0, description="Duración mínima del vuelo en horas")
    duracion_vuelo_max: Optional[int] = Field(None, ge=0, description="Duración máxima del vuelo en horas")
    
    # Alojamientos
    tipo_alojamiento: Optional[Literal["hotel", "hostel", "apartment", "house", "cabin", "resort", "bed_and_breakfast", "villa", "camping"]] = None
    tipo_habitacion: Optional[Literal["single", "double", "triple", "quadruple", "suite", "family", "dormitory", "studio"]] = None
    huespedes_min: Optional[int] = Field(None, ge=1, description="Número mínimo de huéspedes")
    huespedes_max: Optional[int] = Field(None, ge=1, description="Número máximo de huéspedes")
    noches_min: Optional[int] = Field(None, ge=1, description="Estadía mínima en noches")
    amenidades: Optional[List[str]] = Field(None, description="Lista de amenidades requeridas")
    
    # Características de habitación
    bano_privado: Optional[bool] = None
    balcon: Optional[bool] = None
    aire_acondicionado: Optional[bool] = None
    wifi: Optional[bool] = None
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS DE ORDENAMIENTO Y PAGINACIÓN
    # ──────────────────────────────────────────────────────────────
    ordering: Optional[str] = Field(None, description="Campo de ordenamiento (ej: 'precio', '-precio', 'fecha', '-fecha')")
    
    # ──────────────────────────────────────────────────────────────
    # FILTROS AVANZADOS
    # ──────────────────────────────────────────────────────────────
    rating_min: Optional[float] = Field(None, ge=0, le=5, description="Rating mínimo")
    rating_max: Optional[float] = Field(None, ge=0, le=5, description="Rating máximo")
    promociones_solo: Optional[bool] = Field(False, description="Mostrar solo productos con promociones")
    ultima_hora: Optional[bool] = Field(False, description="Mostrar solo ofertas de última hora")
    
    # ──────────────────────────────────────────────────────────────
    # VALIDACIONES
    # ──────────────────────────────────────────────────────────────
    
    @validator('precio_max')
    def validate_precio_max(cls, v, values):
        if v is not None and 'precio_min' in values and values['precio_min'] is not None:
            if v < values['precio_min']:
                raise ValueError('El precio máximo no puede ser menor que el precio mínimo')
        return v
    
    @validator('fecha_max')
    def validate_fecha_max(cls, v, values):
        if v is not None and 'fecha_min' in values and values['fecha_min'] is not None:
            if v < values['fecha_min']:
                raise ValueError('La fecha máxima no puede ser anterior a la fecha mínima')
        return v
    
    @validator('fecha_checkout')
    def validate_fecha_checkout(cls, v, values):
        if v is not None and 'fecha_checkin' in values and values['fecha_checkin'] is not None:
            if v <= values['fecha_checkin']:
                raise ValueError('La fecha de checkout debe ser posterior a la fecha de checkin')
        return v
    
    @validator('fecha_llegada')
    def validate_fecha_llegada(cls, v, values):
        if v is not None and 'fecha_salida' in values and values['fecha_salida'] is not None:
            if v < values['fecha_salida']:
                raise ValueError('La fecha de llegada no puede ser anterior a la fecha de salida')
        return v
    
    @validator('capacidad_max')
    def validate_capacidad_max(cls, v, values):
        if v is not None and 'capacidad_min' in values and values['capacidad_min'] is not None:
            if v < values['capacidad_min']:
                raise ValueError('La capacidad máxima no puede ser menor que la capacidad mínima')
        return v
    
    @validator('duracion_max')
    def validate_duracion_max(cls, v, values):
        if v is not None and 'duracion_min' in values and values['duracion_min'] is not None:
            if v < values['duracion_min']:
                raise ValueError('La duración máxima no puede ser menor que la duración mínima')
        return v
    
    @validator('huespedes_max')
    def validate_huespedes_max(cls, v, values):
        if v is not None and 'huespedes_min' in values and values['huespedes_min'] is not None:
            if v < values['huespedes_min']:
                raise ValueError('El número máximo de huéspedes no puede ser menor que el mínimo')
        return v
    
    @validator('rating_max')
    def validate_rating_max(cls, v, values):
        if v is not None and 'rating_min' in values and values['rating_min'] is not None:
            if v < values['rating_min']:
                raise ValueError('El rating máximo no puede ser menor que el rating mínimo')
        return v

# ──────────────────────────────────────────────────────────────
# FILTROS ESPECÍFICOS POR TIPO DE PRODUCTO
# ──────────────────────────────────────────────────────────────

class FiltroActividades(Schema):
    """Filtros específicos para actividades"""
    nivel_dificultad: Optional[Literal["Very Easy", "Easy", "Medium", "Hard", "Very Hard", "Extreme"]] = None
    incluye_guia: Optional[bool] = None
    idioma: Optional[str] = None
    duracion_min: Optional[int] = Field(None, ge=0, le=24)
    duracion_max: Optional[int] = Field(None, ge=0, le=24)
    fecha_especifica: Optional[date] = None
    hora_inicio: Optional[time] = None

class FiltroVuelos(Schema):
    """Filtros específicos para vuelos"""
    aerolinea: Optional[str] = None
    clase_vuelo: Optional[Literal["Basic Economy", "Economy", "Premium Economy", "Business Class", "First Class"]] = None
    duracion_vuelo_min: Optional[int] = Field(None, ge=0)
    duracion_vuelo_max: Optional[int] = Field(None, ge=0)
    escala_directa: Optional[bool] = None
    terminal: Optional[str] = None

class FiltroAlojamientos(Schema):
    """Filtros específicos para alojamientos"""
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

class FiltroTransporte(Schema):
    """Filtros específicos para transporte"""
    tipo_transporte: Optional[str] = None
    duracion_viaje_min: Optional[int] = Field(None, ge=0)
    duracion_viaje_max: Optional[int] = Field(None, ge=0)

# ──────────────────────────────────────────────────────────────
# FILTROS DE DISPONIBILIDAD
# ──────────────────────────────────────────────────────────────

class FiltroDisponibilidad(Schema):
    """Filtros específicos para disponibilidad"""
    fecha_inicio: date
    fecha_fin: date
    cantidad_personas: Optional[int] = Field(1, ge=1)
    habitaciones: Optional[int] = Field(1, ge=1)
    
    @validator('fecha_fin')
    def validate_fecha_fin(cls, v, values):
        if 'fecha_inicio' in values and v <= values['fecha_inicio']:
            raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v

# ──────────────────────────────────────────────────────────────
# FILTROS DE BÚSQUEDA AVANZADA
# ──────────────────────────────────────────────────────────────

class BusquedaAvanzada(Schema):
    """Filtros para búsqueda avanzada con múltiples criterios"""
    terminos: List[str] = Field(..., description="Lista de términos de búsqueda")
    campos: Optional[List[str]] = Field(None, description="Campos específicos donde buscar")
    operador: Optional[Literal["AND", "OR"]] = Field("OR", description="Operador lógico para combinar términos")
    fuzzy: Optional[bool] = Field(False, description="Búsqueda aproximada")
    
    @validator('campos')
    def validate_campos(cls, v):
        if v is not None:
            campos_validos = ['nombre', 'descripcion', 'aerolinea', 'tipo', 'idioma', 'amenidades']
            for campo in v:
                if campo not in campos_validos:
                    raise ValueError(f'Campo no válido: {campo}. Campos válidos: {campos_validos}')
        return v 