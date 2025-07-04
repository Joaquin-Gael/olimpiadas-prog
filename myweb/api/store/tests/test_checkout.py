import pytest
from api.store.models import Orders, Sales

@pytest.mark.django_db
def test_checkout_and_pay(client_authed, cart_with_items):
    # Checkout del carrito
    r1 = client_authed.post("/cart/checkout/", HTTP_IDEMPOTENCY_KEY="k1")
    assert r1.status_code == 201
    order_id = r1.json()["order_id"]

    # Primer pago (POST, con JSON y header de idempotencia)
    payment_data = {
        "payment_method": "credit_card",
        "card_number": "4111111111111111",
        "expiry_date": "12/30",
        "cvv": "123",
        "cardholder_name": "Test User"
    }
    r2 = client_authed.post(f"/orders/{order_id}/pay", json=payment_data, HTTP_IDEMPOTENCY_KEY="k2")
    assert r2.status_code == 200
    sale_id_1 = r2.json()["sale_id"]
    assert Orders.objects.get(id=order_id).state == "CONFIRMED"
    assert Sales.objects.filter(order_id=order_id).exists()

    # Segundo pago con la misma key (debe ser idempotente)
    r3 = client_authed.post(f"/orders/{order_id}/pay", json=payment_data, HTTP_IDEMPOTENCY_KEY="k2")
    assert r3.status_code == 200
    sale_id_2 = r3.json()["sale_id"]
    assert sale_id_1 == sale_id_2 