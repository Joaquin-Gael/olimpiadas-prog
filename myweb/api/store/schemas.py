from pydantic import BaseModel, Field, PositiveInt
from typing import List, Any
from datetime import datetime

# ── Salidas ────────────────────────────────────────────────────
class CartItemOut(BaseModel):
    id: int
    availability_id: int
    product_metadata_id: int
    qty: PositiveInt
    unit_price: float
    currency: str
    config: Any

class CartOut(BaseModel):
    id: int
    status: str
    items_cnt: int
    total: float
    currency: str
    updated_at: datetime
    items: List[CartItemOut]

# ── Entradas ───────────────────────────────────────────────────
class ItemAddIn(BaseModel):
    availability_id: int
    product_metadata_id: int
    qty: PositiveInt
    unit_price: float                   # precio final por "unidad"
    config: dict = Field(default_factory=dict)

class ItemQtyPatchIn(BaseModel):
    qty: PositiveInt 