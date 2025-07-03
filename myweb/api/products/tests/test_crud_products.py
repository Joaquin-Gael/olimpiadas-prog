import pytest
from datetime import date, timedelta, time
from api.products.models import Activities, ProductsMetadata

@pytest.mark.django_db
def test_crud_activity_product(ninja_client, supplier, location):
    # 1. Create an activity-type product
    payload = {
        "product_type": "activity",
        "unit_price": 200.0,
        "supplier_id": supplier.id,
        "product": {
            "name": "Test Activity CRUD",
            "description": "Test activity for CRUD.",
            "location_id": location.id,
            "date": str(date.today() + timedelta(days=5)),
            "start_time": "09:00:00",
            "duration_hours": 4,
            "include_guide": True,
            "maximum_spaces": 15,
            "difficulty_level": "Easy",
            "language": "Spanish",
            "available_slots": 15
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    assert response.status_code == 200
    data = response.json()
    product_id = data["id"]
    assert data["product_type"] == "activity"
    assert data["unit_price"] == 200.0
    assert data["product"]["name"] == payload["product"]["name"]

    # 2. Retrieve the created product
    response = ninja_client.get(f"/products/{product_id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["product"]["name"] == "Test Activity CRUD"

    # 3. Update the product (name and price)
    update_payload = {
        "unit_price": 250.0,
        "product": {
            "name": "Updated CRUD Activity",
            "description": "Updated description."
        }
    }
    response = ninja_client.patch(f"/products/{product_id}/", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["unit_price"] == 250.0
    assert data["product"]["name"] == "Updated CRUD Activity"
    assert data["product"]["description"] == "Updated description."

    # 4. List products and verify the updated product appears
    response = ninja_client.get("/products/")
    assert response.status_code == 200
    ids = [prod["id"] for prod in response.json()]
    assert product_id in ids

    # 5. Delete (deactivate) the product
    response = ninja_client.delete(f"/products/{product_id}/")
    assert response.status_code == 204

    # 6. Try to retrieve the deactivated product (should fail)
    response = ninja_client.get(f"/products/{product_id}/")
    assert response.status_code in (404, 400)

    # 7. Try to update the deactivated product (should fail)
    response = ninja_client.patch(f"/products/{product_id}/", json=update_payload)
    assert response.status_code in (404, 400)

    # 8. Try to delete again (should fail)
    response = ninja_client.delete(f"/products/{product_id}/")
    assert response.status_code in (404, 400)

    # 9. Create product with invalid data (missing required field)
    invalid_payload = {
        "product_type": "activity",
        "unit_price": 100.0,
        "supplier_id": supplier.id,
        "product": {
            # Missing 'name'
            "description": "No name",
            "location_id": location.id,
            "date": str(date.today() + timedelta(days=2)),
            "start_time": "10:00:00",
            "duration_hours": 2,
            "include_guide": True,
            "maximum_spaces": 10,
            "difficulty_level": "Easy",
            "language": "Spanish",
            "available_slots": 10
        }
    }
    response = ninja_client.post("/products/create/", json=invalid_payload)
    assert response.status_code == 422
    assert "name" in response.content.decode()

    # 10. Create product with invalid value (past date)
    invalid_payload["product"]["name"] = "Invalid activity"
    invalid_payload["product"]["date"] = str(date.today() - timedelta(days=1))
    response = ninja_client.post("/products/create/", json=invalid_payload)
    assert response.status_code == 422
    assert "date" in response.content.decode() 