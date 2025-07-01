from django.core.validators import MinValueValidator
from django.db import models

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
        choices=IdentityDocumentType.choices(),
    )
    identity_document = models.CharField(max_length=255)
    born_date = models.DateField()
    sex = models.CharField(
        choices=SexType.choices(),
    )
    observations = models.TextField()

class Orders(models.Model):
    id = models.AutoField("order_id", primary_key=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    date = models.DateTimeField()
    state = models.CharField(
        choices=OrderTravelPackageStatus.choices(),
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
        help_text="Total de la orden"
    )
    address = models.ForeignKey(Addresses, on_delete=models.CASCADE)
    notes = models.TextField()

class Notifications(models.Model):
    id = models.AutoField("notification_id", primary_key=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    email_destination = models.EmailField()
    subject = models.CharField()
    body = models.TextField()
    date = models.DateTimeField()
    notification_type = models.CharField(
        choices=NotificationType.choices(),
    )
    shipping_state = models.CharField(
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
        choices=PassengerType.choices,
        default=PassengerType.Cl,
    )
    passenger = models.ForeignKey(Companions, on_delete=models.CASCADE, null=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, null=True)
    state = models.CharField(
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
        choices=VoucherState.choices,
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