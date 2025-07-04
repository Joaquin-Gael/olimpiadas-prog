from ninja import Router
from ninja.errors import HttpError

from django.shortcuts import get_object_or_404
from django.db import transaction

from api.core.notification import services as notif_srv

from .services import services_payments as pay_srv
from .services import services_sales as sale_srv
from .services.services_orders import InvalidCartStateError
from .idempotency import store_idempotent
from .models import NotificationType, Orders

router = Router(tags=["Orders"])

@router.patch("/order/{order_id}/pay/", response={200: dict})
@store_idempotent()
@transaction.atomic
def pay_order(request, order_id: int):
    try:
        order = get_object_or_404(Orders, id=order_id, client=request.user)

        if order.state != "PENDING":
            raise HttpError(409, "orden_no_pendiente")

        try:
            result = pay_srv.fake_payment_gateway(order.total)
            if result["status"] != "SUCCESS":
                raise pay_srv.PaymentError()

            sale = sale_srv.register_sale(order, result["gateway_id"])
            order.state = "CONFIRMED"
            order.save(update_fields=["state"])

            notif_srv.send_notification(
                order,
                NotificationType.BOOKING_CONFIRMED,
                "Reserva confirmada",
                f"¡Gracias! Tu reserva #{order.id} quedó confirmada."
            )

        except pay_srv.PaymentError:
            raise HttpError(402, "pago_rechazado")

        return 200, {"sale_id": sale.id, "order_state": order.state}
    except Exception as e:
        return HttpError(500, message=str(e))