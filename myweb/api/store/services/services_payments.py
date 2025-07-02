from decimal import Decimal

class PaymentError(Exception): pass

def fake_payment_gateway(amount: Decimal):
    """
    Mini-simulación. Siempre aprueba si amount > 0.
    """
    if amount <= 0:
        raise PaymentError("invalid_amount")
    return {"status": "SUCCESS", "gateway_id": "FAKE-123"} 