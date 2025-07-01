import pytest
from datetime import date, timedelta

pytestmark = pytest.mark.django_db


class TestPackageCreation:
    """Tests for package creation"""

    def test_create_package_simple(self, ninja_client):
        """Test creating a simple package without components"""
        payload = {
            "name": "Simple Test Package",
            "description": "A test package without components",
            "final_price": 500.0
        }
        response = ninja_client.post("/package/", json=payload)
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response content: {response.content}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Simple Test Package"
        assert data["final_price"] == 500.0
        assert data["components"] == []

    def test_create_package_with_components(self, ninja_client, supplier, location):
        """Test creating a package with components"""
        # First create products to use as components
        activity_payload = {
            "product_type": "activity",
            "unit_price": 100.0,
            "supplier_id": supplier.id,
            "product": {
                "name": "Package Activity",
                "description": "Test activity",
                "location_id": location.id,
                "date": str(date.today() + timedelta(days=5)),
                "start_time": "09:00:00",
                "duration_hours": 3,
                "include_guide": True,
                "maximum_spaces": 10,
                "difficulty_level": "Easy",
                "language": "English",
                "available_slots": 10
            }
        }
        activity_resp = ninja_client.post("/products/create/", json=activity_payload)
        assert activity_resp.status_code == 200
        activity_metadata_id = activity_resp.json()["id"]

        # Create package with component
        package_payload = {
            "name": "Complete Package",
            "description": "Package with included activity",
            "base_price": 400.0,
            "taxes": 50.0,
            "final_price": 450.0,
            "components": [
                {
                    "product_metadata_id": activity_metadata_id,
                    "order": 1,
                    "quantity": 1,
                    "title": "Included Activity",
                    "start_date": str(date.today() + timedelta(days=5))
                }
            ]
        }
        response = ninja_client.post("/package/", json=package_payload)
        print(f"[DEBUG] Package response status: {response.status_code}")
        print(f"[DEBUG] Package response content: {response.content}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Complete Package"
        assert data["final_price"] == 450.0
        assert len(data["components"]) == 1
        assert data["components"][0]["title"] == "Included Activity"

    def test_create_package_invalid_price(self, ninja_client):
        """Test error: final price doesn't match base + taxes"""
        payload = {
            "name": "Error Package",
            "description": "Package with incorrect prices",
            "base_price": 100.0,
            "taxes": 20.0,
            "final_price": 150.0  # Should be 120.0
        }
        response = ninja_client.post("/package/", json=payload)
        assert response.status_code == 422
        # Check for the relevant error message in a robust way
        assert "final price does not match" in response.content.decode().lower()

    def test_create_package_negative_price(self, ninja_client):
        """Test error: negative price"""
        payload = {
            "name": "Error Package",
            "description": "Package with negative price",
            "final_price": -50.0
        }
        response = ninja_client.post("/package/", json=payload)
        assert response.status_code == 422
        assert "greater than 0" in response.content.decode()


class TestPackageCRUD:
    """Tests for package CRUD operations"""

    def test_get_package(self, ninja_client):
        """Test getting a specific package"""
        # Create package
        create_payload = {
            "name": "Package to Get",
            "description": "Package for retrieval test",
            "final_price": 300.0
        }
        create_resp = ninja_client.post("/package/", json=create_payload)
        assert create_resp.status_code == 200
        package_id = create_resp.json()["id"]

        # Get package
        response = ninja_client.get(f"/package/{package_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Package to Get"
        assert data["final_price"] == 300.0

    def test_update_package(self, ninja_client):
        """Test updating a package"""
        # Create package
        create_payload = {
            "name": "Original Package",
            "description": "Original description",
            "final_price": 250.0
        }
        create_resp = ninja_client.post("/package/", json=create_payload)
        assert create_resp.status_code == 200
        package_id = create_resp.json()["id"]

        # Update package
        update_payload = {
            "name": "Updated Package",
            "description": "Updated description",
            "final_price": 350.0
        }
        response = ninja_client.put(f"/package/{package_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Package"
        assert data["description"] == "Updated description"
        assert data["final_price"] == 350.0

    def test_delete_package(self, ninja_client):
        """Test deleting a package (soft delete)"""
        # Create package
        create_payload = {
            "name": "Package to Delete",
            "description": "Package that will be deleted",
            "final_price": 200.0
        }
        create_resp = ninja_client.post("/package/", json=create_payload)
        assert create_resp.status_code == 200
        package_id = create_resp.json()["id"]

        # Delete package
        response = ninja_client.delete(f"/package/{package_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify that deleted package cannot be retrieved
        get_response = ninja_client.get(f"/package/{package_id}")
        assert get_response.status_code == 404


class TestPackageList:
    """Tests for package listing"""

    def test_list_packages(self, ninja_client):
        """Test listing all packages"""
        # Create some packages
        packages = [
            {"name": "Package 1", "description": "Desc 1", "final_price": 100.0},
            {"name": "Package 2", "description": "Desc 2", "final_price": 200.0},
            {"name": "Package 3", "description": "Desc 3", "final_price": 300.0}
        ]
        for pkg in packages:
            ninja_client.post("/package/", json=pkg)

        # List packages
        response = ninja_client.get("/package/")
        assert response.status_code == 200
        data = response.json()
        # Verify that response has paginated structure
        assert "results" in data
        assert "count" in data
        assert len(data["results"]) >= 3

    def test_search_packages_by_name(self, ninja_client):
        """Test searching packages by name"""
        # Create packages with specific names
        packages = [
            {"name": "Adventure Package", "description": "Desc", "final_price": 300.0},
            {"name": "Relax Package", "description": "Desc", "final_price": 400.0},
            {"name": "Cultural Package", "description": "Desc", "final_price": 250.0}
        ]
        for pkg in packages:
            ninja_client.post("/package/", json=pkg)

        # Search by name
        response = ninja_client.get("/package/?name=adventure")
        assert response.status_code == 200
        data = response.json()
        # Verify that response has paginated structure
        assert "results" in data
        assert len(data["results"]) >= 1
        assert "Adventure" in data["results"][0]["name"]

    def test_search_packages_by_price_range(self, ninja_client):
        """Test searching packages by price range"""
        # Create packages with specific prices
        packages = [
            {"name": "Economy Package", "description": "Desc", "final_price": 100.0},
            {"name": "Mid-range Package", "description": "Desc", "final_price": 500.0},
            {"name": "Premium Package", "description": "Desc", "final_price": 1000.0}
        ]
        for pkg in packages:
            ninja_client.post("/package/", json=pkg)

        # Search by price range
        response = ninja_client.get("/package/?min_price=200&max_price=600")
        assert response.status_code == 200
        data = response.json()
        # Verify that response has paginated structure
        assert "results" in data
        assert len(data["results"]) >= 1
        for pkg in data["results"]:
            assert 200 <= pkg["final_price"] <= 600
