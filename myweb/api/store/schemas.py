from pydantic import BaseModel, Field, PositiveInt
from typing import List, Any, Optional
from datetime import datetime, date
from ninja import Schema

from api.products.common.schemas import BaseSchema

# ── Salidas ────────────────────────────────────────────────────
class UserBasicInfo(Schema):
    """Información básica del usuario para respuestas del carrito"""
    id: int
    first_name: str
    last_name: str
    email: str

    class Meta:
        from_attributes = True

class CartItemOut(Schema):
    availability_id: int
    product_metadata_id: int
    qty: PositiveInt
    unit_price: float
    currency: str
    config: Any

    class Meta:
        from_attributes = True

class CartOut(BaseSchema):
    id: int
    user_id: int  # Agregado: ID del usuario propietario del carrito
    user_info: Optional[UserBasicInfo] = None  # Agregado: Información básica del usuario
    status: str
    items_cnt: int
    total: float
    currency: str
    updated_at: datetime
    items: List[CartItemOut]

# ── Schemas para Sales (CORREGIDOS) ────────────────────────────
class SalesOut(Schema):
    """Schema de salida para Sales - Corregido para coincidir con el modelo"""
    id: int
    order_id: int  # Corregido: era 'order', ahora es 'order_id'
    amount: Optional[float] = None  # Agregado: campo opcional del modelo
    total: float
    payment_status: str
    sale_type: str
    payment_type: str
    transaction_number: Optional[int] = None  # Agregado: campo opcional del modelo
    sale_date: datetime
    transaction_id: Optional[str] = None  # Agregado: campo opcional del modelo
    created_at: datetime  # Agregado: campo del modelo
    updated_at: datetime  # Agregado: campo del modelo

# ── Entradas ───────────────────────────────────────────────────
class ItemAddIn(BaseSchema):
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
    #card_number: str = Field(..., min_length=13, max_length=19, description="Número de tarjeta")
    #expiry_date: str = Field(..., pattern=r"^\d{2}/\d{2}$", description="Fecha de vencimiento (MM/YY)")
    #cvv: str = Field(..., min_length=3, max_length=4, description="Código de seguridad")
    #cardholder_name: str = Field(..., min_length=2, description="Nombre del titular")

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

# ── Schemas para Ventas (CORREGIDOS) ────────────────────────────
class SaleOut(BaseModel):
    """Schema de salida para Sale - Corregido para coincidir con el modelo"""
    id: int
    order_id: int  # Corregido: ya estaba bien
    amount: Optional[float] = None  # Corregido: campo opcional del modelo
    total: float  # Agregado: campo requerido del modelo
    payment_status: str  # Corregido: ya estaba bien
    sale_type: str  # Agregado: campo del modelo
    payment_type: str  # Agregado: campo del modelo
    transaction_number: Optional[int] = None  # Agregado: campo opcional del modelo
    sale_date: datetime  # Corregido: era 'created_at', ahora es 'sale_date'
    transaction_id: Optional[str] = None  # Corregido: ya estaba bien
    created_at: datetime  # Agregado: campo del modelo
    updated_at: datetime  # Agregado: campo del modelo

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

class StripeResponse(BaseSchema):
    session_url: str

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

# ── Schemas para Companions ─────────────────────────────────────
class CompanionCreateSchema(BaseModel):
    """Schema para crear un acompañante"""
    first_name: str = Field(..., max_length=64, description="Nombre del acompañante")
    last_name: str = Field(..., max_length=64, description="Apellido del acompañante")
    identity_document_type: str = Field(..., description="Tipo de documento de identidad")
    identity_document: str = Field(..., max_length=255, description="Número del documento")
    born_date: date = Field(..., description="Fecha de nacimiento")
    sex: str = Field(..., description="Sexo (M/F)")
    observations: str = Field(..., description="Observaciones adicionales")

class CompanionUpdateSchema(BaseModel):
    """Schema para actualizar un acompañante"""
    first_name: Optional[str] = Field(None, max_length=64)
    last_name: Optional[str] = Field(None, max_length=64)
    identity_document_type: Optional[str] = Field(None, description="Tipo de documento de identidad")
    identity_document: Optional[str] = Field(None, max_length=255)
    born_date: Optional[date] = Field(None, description="Fecha de nacimiento")
    sex: Optional[str] = Field(None, description="Sexo (M/F)")
    observations: Optional[str] = Field(None, description="Observaciones adicionales")

class CompanionResponseSchema(BaseModel):
    """Schema de respuesta para acompañantes"""
    id: int
    first_name: str
    last_name: str
    identity_document_type: str
    identity_document: str
    born_date: date
    sex: str
    observations: str

    class Config:
        from_attributes = True

# ── Schemas para OrderDetails ───────────────────────────────────
class OrderDetailCreateSchema(BaseModel):
    """Schema para crear un detalle de orden"""
    order_id: int = Field(..., description="ID de la orden")
    product_metadata_id: int = Field(..., description="ID del metadata del producto")
    package_id: int = Field(..., description="ID del paquete")
    availability_id: int = Field(..., description="ID de la disponibilidad")
    quantity: int = Field(..., ge=0, description="Cantidad del producto")
    unit_price: float = Field(..., ge=0, description="Precio unitario")
    subtotal: float = Field(..., ge=0, description="Subtotal del detalle")
    discount_applied: float = Field(default=0, ge=0, description="Descuento aplicado")

class OrderDetailResponseSchema(BaseModel):
    """Schema de respuesta para detalles de orden"""
    id: int
    order_id: int
    product_metadata_id: int
    package_id: int
    availability_id: int
    quantity: int
    unit_price: float
    subtotal: float
    discount_applied: float

    class Config:
        from_attributes = True

# ── Schemas para Vouchers ───────────────────────────────────────
class VoucherCreateSchema(BaseModel):
    """Schema para crear un voucher"""
    sale_id: int = Field(..., description="ID de la venta")
    emission_date: datetime = Field(..., description="Fecha de emisión")
    voucher_code: str = Field(..., max_length=128, description="Código del voucher")
    passenger_type: str = Field(..., description="Tipo de pasajero (CLIENT/COMPANY)")
    passenger_id: Optional[int] = Field(None, description="ID del acompañante")
    user_id: Optional[int] = Field(None, description="ID del usuario")
    state: str = Field(default="AVAILABLE", description="Estado del voucher")

class VoucherUpdateSchema(BaseModel):
    """Schema para actualizar un voucher"""
    emission_date: Optional[datetime] = Field(None, description="Fecha de emisión")
    voucher_code: Optional[str] = Field(None, max_length=128, description="Código del voucher")
    passenger_type: Optional[str] = Field(None, description="Tipo de pasajero")
    passenger_id: Optional[int] = Field(None, description="ID del acompañante")
    user_id: Optional[int] = Field(None, description="ID del usuario")
    state: Optional[str] = Field(None, description="Estado del voucher")

class VoucherResponseSchema(BaseModel):
    """Schema de respuesta para vouchers"""
    id: int
    sale_id: int
    emission_date: datetime
    voucher_code: str
    passenger_type: str
    passenger_id: Optional[int]
    user_id: Optional[int]
    state: str

    class Config:
        from_attributes = True

# ── Schemas para VoucherDetails ──────────────────────────────────
class VoucherDetailCreateSchema(BaseModel):
    """Schema para crear un detalle de voucher"""
    voucher_id: int = Field(..., description="ID del voucher")
    product_metadata_id: int = Field(..., description="ID del metadata del producto")
    package_id: int = Field(..., description="ID del paquete")
    service_name: str = Field(..., max_length=32, description="Nombre del servicio")
    product_type: str = Field(..., description="Tipo de producto")
    quantity: int = Field(..., ge=0, description="Cantidad")
    order: str = Field(..., max_length=32, description="Orden del servicio")

class VoucherDetailResponseSchema(BaseModel):
    """Schema de respuesta para detalles de voucher"""
    id: int
    voucher_id: int
    product_metadata_id: int
    package_id: int
    service_name: str
    product_type: str
    quantity: int
    order: str

    class Config:
        from_attributes = True

# ── Schemas para Bills ───────────────────────────────────────────
class BillCreateSchema(BaseModel):
    """Schema para crear una factura"""
    sale_id: int = Field(..., description="ID de la venta")
    bill_number: int = Field(..., ge=1, description="Número de factura")
    emission_date: datetime = Field(..., description="Fecha de emisión")
    user_id: Optional[int] = Field(None, description="ID del usuario")
    items_details: str = Field(..., description="Detalles de los items")
    total: float = Field(..., ge=0, description="Total de la factura")
    state: str = Field(default="DRAFT", description="Estado de la factura")
    bill_type: str = Field(default="STANDARD", description="Tipo de factura")

class BillUpdateSchema(BaseModel):
    """Schema para actualizar una factura"""
    bill_number: Optional[int] = Field(None, ge=1, description="Número de factura")
    emission_date: Optional[datetime] = Field(None, description="Fecha de emisión")
    user_id: Optional[int] = Field(None, description="ID del usuario")
    items_details: Optional[str] = Field(None, description="Detalles de los items")
    total: Optional[float] = Field(None, ge=0, description="Total de la factura")
    state: Optional[str] = Field(None, description="Estado de la factura")
    bill_type: Optional[str] = Field(None, description="Tipo de factura")

class BillResponseSchema(BaseModel):
    """Schema de respuesta para facturas"""
    id: int
    sale_id: int
    bill_number: int
    emission_date: datetime
    user_id: Optional[int]
    items_details: str
    total: float
    state: str
    bill_type: str

    class Config:
        from_attributes = True

# ── Schemas para Notifications ───────────────────────────────────
class NotificationCreateSchema(BaseModel):
    """Schema para crear una notificación"""
    order_id: int = Field(..., description="ID de la orden")
    email_destination: str = Field(..., description="Email de destino")
    subject: str = Field(..., max_length=255, description="Asunto de la notificación")
    body: str = Field(..., description="Cuerpo de la notificación")
    date: datetime = Field(..., description="Fecha de la notificación")
    notification_type: str = Field(..., description="Tipo de notificación")
    shipping_state: str = Field(..., description="Estado de envío")

class NotificationResponseSchema(BaseModel):
    """Schema de respuesta para notificaciones"""
    id: int
    order_id: int
    email_destination: str
    subject: str
    body: str
    date: datetime
    notification_type: str
    shipping_state: str

    class Config:
        from_attributes = True

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
