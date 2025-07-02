from decimal import Decimal
from django.utils import timezone
from ..models import Sales, PaymentStatus, PaymentType

def register_sale(order, gateway_id: str):
    return Sales.objects.create(
        order              = order,
        transaction_number = gateway_id,
        sale_date          = timezone.now(),
        total              = order.total,
        payment_status     = PaymentStatus.PAID_ONLINE,
        payment_type       = PaymentType.ONLINE,
    ) 