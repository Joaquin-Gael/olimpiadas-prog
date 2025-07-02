import pytest
from datetime import date, timedelta, time
from api.products.models import Activities, ProductsMetadata

@pytest.mark.django_db
def test_crud_activity_product(ninja_client, supplier, location):
    # 1. Crear un producto tipo actividad
    payload = {
        "product_type": "activity",
        "unit_price": 200.0,
        "supplier_id": supplier.id,
        "product": {
            "name": "Test Activity CRUD",
            "description": "Actividad de prueba para CRUD.",
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

    # 2. Obtener el producto creado
    response = ninja_client.get(f"/products/{product_id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["product"]["name"] == "Test Activity CRUD"

    # 3. Actualizar el producto (nombre y precio)
    update_payload = {
        "unit_price": 250.0,
        "product": {
            "name": "Actividad CRUD Actualizada",
            "description": "Descripción actualizada."
        }
    }
    response = ninja_client.patch(f"/products/{product_id}/", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["unit_price"] == 250.0
    assert data["product"]["name"] == "Actividad CRUD Actualizada"
    assert data["product"]["description"] == "Descripción actualizada."

    # 4. Listar productos y verificar que el producto actualizado aparece
    response = ninja_client.get("/products/")
    assert response.status_code == 200
    ids = [prod["id"] for prod in response.json()]
    assert product_id in ids

    # 5. Borrar (desactivar) el producto
    response = ninja_client.delete(f"/products/{product_id}/")
    assert response.status_code == 204

    # 6. Intentar obtener el producto desactivado (debe fallar)
    response = ninja_client.get(f"/products/{product_id}/")
    assert response.status_code in (404, 400)

    # 7. Intentar actualizar el producto desactivado (debe fallar)
    response = ninja_client.patch(f"/products/{product_id}/", json=update_payload)
    assert response.status_code in (404, 400)

    # 8. Intentar borrar de nuevo (debe fallar)
    response = ninja_client.delete(f"/products/{product_id}/")
    assert response.status_code in (404, 400)

    # 9. Crear producto con datos inválidos (falta campo requerido)
    invalid_payload = {
        "product_type": "activity",
        "unit_price": 100.0,
        "supplier_id": supplier.id,
        "product": {
            # Falta 'name'
            "description": "Sin nombre",
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

    # 10. Crear producto con valor inválido (fecha pasada)
    invalid_payload["product"]["name"] = "Actividad inválida"
    invalid_payload["product"]["date"] = str(date.today() - timedelta(days=1))
    response = ninja_client.post("/products/create/", json=invalid_payload)
    assert response.status_code == 422
    assert "date" in response.content.decode() 