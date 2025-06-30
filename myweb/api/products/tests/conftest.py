import pytest
from django.contrib.auth import get_user_model
from api.products.models import Suppliers, Location
from datetime import date

@pytest.fixture
def supplier():
    """Crear un proveedor de prueba"""
    return Suppliers.objects.create(
        first_name="Juan",
        last_name="Pérez",
        organization_name="Aventuras del Sur",
        description="Empresa de turismo aventura",
        street="Av. San Martín",
        street_number=123,
        city="Bariloche",
        country="Argentina",
        email="juan@aventurasdelsur.com",
        telephone="+54 294 1234567",
        website="https://aventurasdelsur.com"
    )

@pytest.fixture
def location():
    """Crear una ubicación de prueba"""
    return Location.objects.create(
        country="Argentina",
        state="Río Negro",
        city="Bariloche"
    ) 