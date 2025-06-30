import pytest
from datetime import date, timedelta

pytestmark = pytest.mark.django_db


class TestPackageCreation:
    """Tests para la creación de paquetes"""

    def test_create_package_simple(self, ninja_client):
        """Test crear un paquete simple sin componentes"""
        payload = {
            "name": "Paquete Test Simple",
            "description": "Un paquete de prueba sin componentes",
            "final_price": 500.0
        }
        response = ninja_client.post("/package/", json=payload)
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response content: {response.content}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Paquete Test Simple"
        assert data["final_price"] == 500.0
        assert data["components"] == []

    def test_create_package_with_components(self, ninja_client, supplier, location):
        """Test crear un paquete con componentes"""
        # Primero crear productos para usar como componentes
        activity_payload = {
            "product_type": "activity",
            "unit_price": 100.0,
            "supplier_id": supplier.id,
            "product": {
                "name": "Actividad para Paquete",
                "description": "Actividad de prueba",
                "location_id": location.id,
                "date": str(date.today() + timedelta(days=5)),
                "start_time": "09:00:00",
                "duration_hours": 3,
                "include_guide": True,
                "maximum_spaces": 10,
                "difficulty_level": "Easy",
                "language": "Español",
                "available_slots": 10
            }
        }
        activity_resp = ninja_client.post("/products/create/", json=activity_payload)
        assert activity_resp.status_code == 200
        activity_metadata_id = activity_resp.json()["id"]

        # Crear paquete con componente
        package_payload = {
            "name": "Paquete Completo",
            "description": "Paquete con actividad incluida",
            "base_price": 400.0,
            "taxes": 50.0,
            "final_price": 450.0,
            "components": [
                {
                    "product_metadata_id": activity_metadata_id,
                    "order": 1,
                    "quantity": 1,
                    "title": "Actividad Incluida",
                    "start_date": str(date.today() + timedelta(days=5))
                }
            ]
        }
        response = ninja_client.post("/package/", json=package_payload)
        print(f"[DEBUG] Package response status: {response.status_code}")
        print(f"[DEBUG] Package response content: {response.content}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Paquete Completo"
        assert data["final_price"] == 450.0
        assert len(data["components"]) == 1
        assert data["components"][0]["title"] == "Actividad Incluida"

    def test_create_package_invalid_price(self, ninja_client):
        """Test error: precio final no coincide con base + impuestos"""
        payload = {
            "name": "Paquete Error",
            "description": "Paquete con precios incorrectos",
            "base_price": 100.0,
            "taxes": 20.0,
            "final_price": 150.0  # Debería ser 120.0
        }
        response = ninja_client.post("/package/", json=payload)
        assert response.status_code == 422
        assert "precio final no coincide" in response.content.decode()

    def test_create_package_negative_price(self, ninja_client):
        """Test error: precio negativo"""
        payload = {
            "name": "Paquete Error",
            "description": "Paquete con precio negativo",
            "final_price": -50.0
        }
        response = ninja_client.post("/package/", json=payload)
        assert response.status_code == 422
        assert "greater than 0" in response.content.decode()


class TestPackageCRUD:
    """Tests para CRUD de paquetes"""

    def test_get_package(self, ninja_client):
        """Test obtener un paquete específico"""
        # Crear paquete
        create_payload = {
            "name": "Paquete para Obtener",
            "description": "Paquete para test de obtención",
            "final_price": 300.0
        }
        create_resp = ninja_client.post("/package/", json=create_payload)
        assert create_resp.status_code == 200
        package_id = create_resp.json()["id"]

        # Obtener paquete
        response = ninja_client.get(f"/package/{package_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Paquete para Obtener"
        assert data["final_price"] == 300.0

    def test_update_package(self, ninja_client):
        """Test actualizar un paquete"""
        # Crear paquete
        create_payload = {
            "name": "Paquete Original",
            "description": "Descripción original",
            "final_price": 250.0
        }
        create_resp = ninja_client.post("/package/", json=create_payload)
        assert create_resp.status_code == 200
        package_id = create_resp.json()["id"]

        # Actualizar paquete
        update_payload = {
            "name": "Paquete Actualizado",
            "description": "Descripción actualizada",
            "final_price": 350.0
        }
        response = ninja_client.put(f"/package/{package_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Paquete Actualizado"
        assert data["description"] == "Descripción actualizada"
        assert data["final_price"] == 350.0

    def test_delete_package(self, ninja_client):
        """Test eliminar un paquete (soft delete)"""
        # Crear paquete
        create_payload = {
            "name": "Paquete a Eliminar",
            "description": "Paquete que será eliminado",
            "final_price": 200.0
        }
        create_resp = ninja_client.post("/package/", json=create_payload)
        assert create_resp.status_code == 200
        package_id = create_resp.json()["id"]

        # Eliminar paquete
        response = ninja_client.delete(f"/package/{package_id}")
        assert response.status_code == 200
        assert "eliminado correctamente" in response.json()["message"]

        # Verificar que no se puede obtener el paquete eliminado
        get_response = ninja_client.get(f"/package/{package_id}")
        assert get_response.status_code == 404


class TestPackageList:
    """Tests para listado de paquetes"""

    def test_list_packages(self, ninja_client):
        """Test listar todos los paquetes"""
        # Crear algunos paquetes
        packages = [
            {"name": "Paquete 1", "description": "Desc 1", "final_price": 100.0},
            {"name": "Paquete 2", "description": "Desc 2", "final_price": 200.0},
            {"name": "Paquete 3", "description": "Desc 3", "final_price": 300.0}
        ]
        for pkg in packages:
            ninja_client.post("/package/", json=pkg)

        # Listar paquetes
        response = ninja_client.get("/package/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) >= 3

    def test_search_packages_by_name(self, ninja_client):
        """Test búsqueda de paquetes por nombre"""
        # Crear paquetes con nombres específicos
        packages = [
            {"name": "Paquete Aventura", "description": "Desc", "final_price": 300.0},
            {"name": "Paquete Relax", "description": "Desc", "final_price": 400.0},
            {"name": "Paquete Cultural", "description": "Desc", "final_price": 250.0}
        ]
        for pkg in packages:
            ninja_client.post("/package/", json=pkg)

        # Buscar por nombre
        response = ninja_client.get("/package/?name=aventura")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) >= 1
        assert "Aventura" in data["results"][0]["name"]

    def test_search_packages_by_price_range(self, ninja_client):
        """Test búsqueda de paquetes por rango de precio"""
        # Crear paquetes con precios específicos
        packages = [
            {"name": "Paquete Económico", "description": "Desc", "final_price": 100.0},
            {"name": "Paquete Medio", "description": "Desc", "final_price": 500.0},
            {"name": "Paquete Premium", "description": "Desc", "final_price": 1000.0}
        ]
        for pkg in packages:
            ninja_client.post("/package/", json=pkg)

        # Buscar por rango de precio
        response = ninja_client.get("/package/?min_price=200&max_price=600")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) >= 1
        for pkg in data["results"]:
            assert 200 <= pkg["final_price"] <= 600
