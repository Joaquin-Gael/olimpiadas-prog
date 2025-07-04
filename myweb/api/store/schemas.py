from pydantic import BaseModel, Field, PositiveInt
from typing import List, Any, Optional
from datetime import datetime
from decimal import Decimal

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

# ── Schemas para Órdenes ───────────────────────────────────────
class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    total: float
    created_at: datetime

class OrderOut(BaseModel):
    id: int
    total: float
    state: str
    created_at: datetime
    updated_at: datetime
    user_id: int
    items_count: int
    items: Optional[List[OrderItemOut]] = None

class OrderListOut(BaseModel):
    id: int
    total: float
    state: str
    created_at: datetime
    user_id: int

class OrderCreateIn(BaseModel):
    cart_id: int = Field(..., description="ID del carrito a convertir en orden")

class OrderCancelIn(BaseModel):
    reason: Optional[str] = Field(None, description="Razón opcional de la cancelación")

# ── Schemas para Pagos ─────────────────────────────────────────
class PaymentMethodIn(BaseModel):
    payment_method: str = Field(..., description="Método de pago (credit_card, debit_card, etc.)")
    card_number: str = Field(..., min_length=13, max_length=19, description="Número de tarjeta")
    expiry_date: str = Field(..., pattern=r"^\d{2}/\d{2}$", description="Fecha de vencimiento (MM/YY)")
    cvv: str = Field(..., min_length=3, max_length=4, description="Código de seguridad")
    cardholder_name: str = Field(..., min_length=2, description="Nombre del titular")

class PaymentOut(BaseModel):
    sale_id: int
    transaction_id: str
    amount: float
    payment_status: str
    order_id: int
    payment_method: str
    created_at: datetime

class PaymentStatusOut(BaseModel):
    order_id: int
    payment_status: str
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    payment_method: Optional[str] = None
    message: Optional[str] = None

# ── Schemas para Ventas ────────────────────────────────────────
class SaleOut(BaseModel):
    id: int
    order_id: int
    amount: float
    payment_method: str
    payment_status: str
    transaction_id: str
    created_at: datetime

class SaleSummaryOut(BaseModel):
    total_sales: int
    total_amount: float
    recent_sales_count: int
    recent_sales_amount: float
    average_amount: float

class SaleStatisticsOut(BaseModel):
    total_sales: int
    total_amount: float
    average_amount: float
    payment_methods: List[dict]

# ── Schemas para Reembolsos ────────────────────────────────────
class RefundIn(BaseModel):
    amount: Optional[float] = Field(None, description="Monto a reembolsar (si es None, reembolsa todo)")

class RefundOut(BaseModel):
    message: str
    sale_id: int
    refunded_amount: float
    refund_id: Optional[str] = None

# ── Schemas para Respuestas de Error ───────────────────────────
class ErrorResponse(BaseModel):
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None

class SuccessResponse(BaseModel):
    message: str
    data: Optional[dict] = None

# ── Schemas para Filtros y Paginación ──────────────────────────
class OrderFilterIn(BaseModel):
    state: Optional[str] = Field(None, description="Filtrar por estado de orden")
    start_date: Optional[datetime] = Field(None, description="Fecha de inicio para filtrar")
    end_date: Optional[datetime] = Field(None, description="Fecha de fin para filtrar")
    limit: int = Field(10, ge=1, le=100, description="Límite de resultados")

class PaginationOut(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_previous: bool

# ── Schemas para Notificaciones ────────────────────────────────
class NotificationOut(BaseModel):
    id: int
    order_id: int
    type: str
    subject: str
    sent_at: datetime
    status: str

# ── Schemas para Validación ────────────────────────────────────
class IdempotencyHeader(BaseModel):
    HTTP_IDEMPOTENCY_KEY: str = Field(..., description="Clave de idempotencia requerida")

# ── Schemas para Reportes ──────────────────────────────────────
class SalesReportIn(BaseModel):
    start_date: datetime = Field(..., description="Fecha de inicio del reporte")
    end_date: datetime = Field(..., description="Fecha de fin del reporte")
    group_by: Optional[str] = Field("day", description="Agrupar por: day, week, month")

class SalesReportOut(BaseModel):
    period: str
    total_sales: int
    total_amount: float
    average_order_value: float
    top_products: List[dict]
    payment_methods_breakdown: List[dict] 