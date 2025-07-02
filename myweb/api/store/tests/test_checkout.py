import pytest
from api.store.models import Orders, Sales

@pytest.mark.django_db
def test_checkout_and_pay(client_authed, cart_with_items):
    r1 = client_authed.post("/cart/checkout/", HTTP_IDEMPOTENCY_KEY="k1")
    assert r1.status_code == 201
    order_id = r1.json()["order_id"]

    r2 = client_authed.patch(f"/order/{order_id}/pay/", HTTP_IDEMPOTENCY_KEY="k2")
    assert r2.status_code == 200
    assert Orders.objects.get(id=order_id).state == "CONFIRMED"
    assert Sales.objects.filter(order_id=order_id).exists() 