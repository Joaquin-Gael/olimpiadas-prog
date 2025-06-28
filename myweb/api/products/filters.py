# api/products/filters.py
from ninja import Schema
from typing import Literal, Optional
from datetime import date

class ProductosFiltro(Schema):
    tipo: Optional[Literal["actividad", "vuelo", "alojamiento", "transporte"]] = None
    destino_id: Optional[int] = None
    origen_id: Optional[int] = None
    fecha_min: Optional[date] = None
    fecha_max: Optional[date] = None
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None
    supplier_id: Optional[int] = None
    search: Optional[str] = None
    ordering: Optional[str] = None  # ej. "-precio"
