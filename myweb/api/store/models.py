from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from decimal import Decimal

from enum import Enum

from api.clients.models import IdentityDocumentType, Clients, Addresses
from api.products.models import ProductsMetadata, Packages, ProductType

class SexType(Enum):
    M = "M"
    F = "F"

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]

class OrderTravelPackageStatus(str, Enum):
    PENDING       = "Pending"
    CONFIRMED     = "Confirmed"
    UPCOMING      = "Upcoming"
    IN_PROGRESS   = "In Progress"
    COMPLETED     = "Completed"
    CANCELLED     = "Cancelled"
    REFUNDED      = "Refunded"

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]

class NotificationType(Enum):
    BOOKING_PENDING       = ("BOOKING_PENDING",       "Booking Pending")
    BOOKING_CONFIRMED     = ("BOOKING_CONFIRMED",     "Booking Confirmed")
    TRIP_UPCOMING_REMINDER = ("TRIP_UPCOMING_REMINDER","Upcoming Trip Reminder")
    TRIP_STARTED          = ("TRIP_STARTED",          "Trip Started")
    TRIP_COMPLETED        = ("TRIP_COMPLETED",        "Trip Completed")
    BOOKING_CANCELLED     = ("BOOKING_CANCELLED",     "Booking Cancelled")
    REFUND_ISSUED         = ("REFUND_ISSUED",         "Refund Issued")

    @classmethod
    def choices(cls):
        return [tag.value for tag in cls]


class PaymentStatus(models.TextChoices):
    DUE       = "DUE", "Due"
    PAID_CASH = "PAID_CASH", "Paid (Cash)"
    PAID_CHEQUE = "PAID_CHEQUE", "Paid (Cheque)"
    PAID_ONLINE = "PAID_ONLINE", "Paid (Online)"
    CANCELLED = "CANCELLED", "Cancelled"

class SaleType(models.TextChoices):
    RETAIL    = "RETAIL", "Retail"
    WHOLESALE = "WHOLESALE", "Wholesale"
    ONLINE    = "ONLINE", "Online"
    IN_STORE  = "IN_STORE", "In‑Store"
    BACKORDER = "BACKORDER", "Backorder"

class PaymentType(models.TextChoices):
    CASH         = "CASH", "Cash"
    CHEQUE       = "CHEQUE", "Cheque"
    CREDIT_CARD  = "CREDIT_CARD", "Credit Card"
    DEBIT_CARD   = "DEBIT_CARD", "Debit Card"
    ONLINE       = "ONLINE", "Online Payment"
    WIRE_TRANSFER = "WIRE_TRANSFER", "Wire Transfer"

class PassengerType(models.TextChoices):
    Cl = "CLIENT", "Client"
    CO = "COMPANY", "Companion"

class VoucherState(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Available"     # Vale creado y listo para asignarse
    ISSUED    = "ISSUED",    "Issued"        # Vale entregado a un destinatario
    REDEEMED  = "REDEEMED",  "Redeemed"      # Vale ya utilizado :contentReference[oaicite:1]{index=1}
    EXPIRED   = "EXPIRED",   "Expired"       # Fecha de caducidad superada :contentReference[oaicite:2]{index=2}
    RETRACTED = "RETRACTED", "Retracted"     # Vale devuelto al emisor (cancelado) :contentReference[oaicite:3]{index=3}

class InvoiceState(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    UNPAID = "UNPAID", "Unpaid"
    SCHEDULED = "SCHEDULED", "Scheduled"
    PARTIALLY_PAID = "PARTIALLY_PAID", "Partially Paid"
    PAID = "PAID", "Paid"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", "Partially Refunded"
    REFUNDED = "REFUNDED", "Refunded"
    CANCELED = "CANCELED", "Canceled"
    FAILED = "FAILED", "Failed"

    # Basado en Square API: DRAFT, UNPAID, SCHEDULED, PARTIALLY_PAID, PAID, PARTIALLY_REFUNDED, REFUNDED, CANCELED, FAILED :contentReference[oaicite:1]{index=1}

class OrderState(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    UPCOMING = "UPCOMING", "Upcoming"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    REFUNDED = "REFUNDED", "Refunded"

class BillType(models.TextChoices):
    STANDARD = "STANDARD", "Standard"
    PROFORMA = "PROFORMA", "Pro Forma"
    INTERIM = "INTERIM", "Interim"
    FINAL = "FINAL", "Final"
    RECURRING = "RECURRING", "Recurring"
    CREDIT = "CREDIT", "Credit"
    DEBIT = "DEBIT", "Debit"
    TIMESHEET = "TIMESHEET", "Timesheet"
    COMMERCIAL = "COMMERCIAL", "Commercial"
    EXPENSE = "EXPENSE", "Expense"
    COMPOSITE = "COMPOSITE", "Composite"
    PAST_DUE = "PAST_DUE", "Past Due"

    # Basado en tipos comunes: pro forma, interim, final, recurring, credit, debit, timesheet, commercial, expense, composite, past due :contentReference[oaicite:2]{index=2}

class Companions(models.Model):
    id = models.AutoField("companion_id" ,primary_key=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    identity_document_type = models.CharField(
        max_length=64,
        choices=IdentityDocumentType.choices(),
    )
    identity_document = models.CharField(max_length=255)
    born_date = models.DateField()
    sex = models.CharField(
        max_length=8,
        choices=SexType.choices(),
    )
    observations = models.TextField()

class Orders(models.Model):
    id = models.AutoField("order_id", primary_key=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    date = models.DateTimeField()
    state = models.CharField(
        max_length=32,
        choices=OrderState.choices,
        default=OrderState.PENDING
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
        help_text="Total de la orden"
    )
    idempotency_key = models.CharField(max_length=64, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Notifications(models.Model):
    id = models.AutoField("notification_id", primary_key=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    email_destination = models.EmailField()
    subject = models.CharField(
        max_length=255  
    )
    body = models.TextField()
    date = models.DateTimeField()
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.choices(),
    )
    shipping_state = models.CharField(
        max_length=32,
        choices=OrderTravelPackageStatus.choices(),
    )

class Sales(models.Model):
    id = models.AutoField("sale_id", primary_key=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    transaction_number = models.IntegerField()
    sale_date = models.DateTimeField()
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
        help_text="Total de la venta"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.DUE
    )
    sale_type = models.CharField(
        max_length=20,
        choices=SaleType.choices,
        default=SaleType.RETAIL
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.ONLINE
    )

class OrderDetails(models.Model):
    id = models.AutoField("order_detail_id", primary_key=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    product_metadata = models.ForeignKey(ProductsMetadata, on_delete=models.CASCADE)
    package = models.ForeignKey(Packages, on_delete=models.CASCADE)
    availability_id = models.PositiveIntegerField(
        help_text="ID de la disponibilidad específica (ActivityAvailability, RoomAvailability, etc.)"
    )
    quantity = models.IntegerField(
        validators=[
            MinValueValidator(0),
        ]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
        help_text="Precio unitario del producto"
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
        help_text="Subtotal del detalle"
    )
    discount_applied = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
        help_text="Descuento aplicado"
    )

class Vouchers(models.Model):
    id = models.AutoField("voucher_id", primary_key=True)
    sale = models.ForeignKey(Sales, on_delete=models.CASCADE)
    emission_date = models.DateTimeField()
    voucher_code = models.CharField(max_length=128)
    passenger_type = models.CharField(
        max_length=32,
        choices=PassengerType.choices,
        default=PassengerType.Cl,
    )
    passenger = models.ForeignKey(Companions, on_delete=models.CASCADE, null=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, null=True)
    state = models.CharField(
        max_length=32,
        choices=VoucherState.choices,
        default=VoucherState.AVAILABLE,
    )


class VoucherDetails(models.Model):
    id = models.AutoField("voucher_detail_id", primary_key=True)
    voucher = models.ForeignKey(Vouchers, on_delete=models.CASCADE)
    product_metadata = models.ForeignKey(ProductsMetadata, on_delete=models.CASCADE)
    package = models.ForeignKey(Packages, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=32)
    product_type = models.CharField(
        max_length=32,
        choices=ProductType.choices,
    )
    quantity = models.IntegerField(
        validators=[
            MinValueValidator(0),
        ]
    )
    order = models.CharField(max_length=32)

class Bills(models.Model):
    id = models.AutoField("bill_id", primary_key=True)
    sale = models.ForeignKey(Sales, on_delete=models.CASCADE)
    bill_number = models.PositiveIntegerField()
    emission_date = models.DateTimeField()
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, null=True)
    items_details = models.TextField()
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
        help_text="Total de la factura"
    )
    state = models.CharField(
        max_length=20,
        choices=InvoiceState.choices,
        default=InvoiceState.DRAFT
    )
    bill_type = models.CharField(
        max_length=15,
        choices=BillType.choices,
        default=BillType.STANDARD
    )

class CartStatus(models.TextChoices):
        OPEN = "OPEN", "Open"
        ORDERED = "ORDERED", "Ordered"
        EXPIRED = "EXPIRED", "Expired"

class Cart(models.Model):
    """Un carrito abierto por un cliente autenticado."""

    id         = models.AutoField(primary_key=True)
    client     = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name="carts")
    status     = models.CharField(max_length=8, choices=CartStatus.choices, default=CartStatus.OPEN)
    currency   = models.CharField(max_length=3, default="USD")       # 1 moneda por carrito
    total      = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    items_cnt  = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["client", "status"])]

    def __str__(self):
        return f"Cart {self.id} ({self.client}) – {self.status}"

class CartItem(models.Model):
    """Un ítem del carrito vinculado a una Availability concreta."""
    cart                = models.ForeignKey(Cart, on_delete=models.CASCADE,
                                            related_name="items")
    availability_id     = models.PositiveIntegerField()              # FK "manual" al servicio reserve_*
    product_metadata_id = models.PositiveIntegerField()              # para info / precio
    qty                 = models.PositiveIntegerField()              # habitaciones / seats / etc.
    unit_price          = models.DecimalField(max_digits=12, decimal_places=2)  # precio TOTAL del ítem (ya multiplicado por noches si aplica)
    currency            = models.CharField(max_length=3)
    config              = models.JSONField(default=dict)             # fechas, horario, etc.
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["cart", "availability_id"]                # evita duplicar línea

class StoreIdempotencyRecord(models.Model):

    class Status(models.IntegerChoices):
        IN_PROGRESS = 0, "In progress"
        COMPLETED   = 1, "Completed"
        FAILED      = 2, "Failed"

    key      = models.CharField(max_length=64)
    user     = models.ForeignKey(
        Clients, on_delete=models.CASCADE, null=True, blank=True
    )
    method   = models.CharField(max_length=6)
    path     = models.CharField(max_length=256)
    status   = models.PositiveSmallIntegerField(
        choices=Status.choices, default=Status.IN_PROGRESS
    )
    response   = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["key", "user", "method", "path"]
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.key} • {self.method} {self.path} ({self.get_status_display()})"
