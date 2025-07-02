import pytest
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from api.products.models import Suppliers, Location, Activities, ProductsMetadata
from django.contrib.contenttypes.models import ContentType
from ninja.testing import TestClient
from datetime import date, timedelta
from myweb.urls import api as ninja_api
from uuid import uuid4

# --- TESTS DE SUPPLIERS ---
@pytest.mark.django_db
def test_create_supplier():
    supplier = Suppliers.objects.create(
        first_name="Ana",
        last_name="García",
        organization_name="Turismo Patagonia",
        description="Operador de turismo en la Patagonia",
        street="Mitre",
        street_number=100,
        city="San Carlos de Bariloche",
        country="Argentina",
        email="ana@patagonia.com",
        telephone="+54 294 5555555",
        website="https://patagonia.com"
    )
    assert supplier.id is not None
    assert supplier.organization_name == "Turismo Patagonia"
    assert supplier.deleted_at is None

@pytest.mark.django_db
def test_create_supplier_duplicate_email():
    Suppliers.objects.create(
        first_name="Ana",
        last_name="García",
        organization_name="Turismo Patagonia",
        description="Operador de turismo en la Patagonia",
        street="Mitre",
        street_number=100,
        city="San Carlos de Bariloche",
        country="Argentina",
        email="ana@patagonia.com",
        telephone="+54 294 5555555",
        website="https://patagonia.com"
    )
    with pytest.raises(IntegrityError):
        Suppliers.objects.create(
            first_name="Juan",
            last_name="Pérez",
            organization_name="Turismo Norte",
            description="Operador de turismo en el norte",
            street="Belgrano",
            street_number=200,
            city="Salta",
            country="Argentina",
            email="ana@patagonia.com",  # Duplicado
            telephone="+54 387 1234567",
            website="https://norte.com"
        )

# --- TESTS DE LOCATION ---
@pytest.mark.django_db
def test_create_location():
    location = Location.objects.create(
        country="Argentina",
        state="Neuquén",
        city="Villa La Angostura"
    )
    assert location.id is not None
    assert location.city == "Villa La Angostura"

# --- TESTS DE PRODUCTO CON CUPO > 0 ---
@pytest.mark.django_db
def test_create_activity_with_available_slots(supplier, location):
    activity = Activities.objects.create(
        name="Rafting en el Limay",
        description="Aventura de rafting para toda la familia",
        location=location,
        date=date.today() + timedelta(days=5),
        start_time="09:00:00",
        duration_hours=3,
        include_guide=True,
        maximum_spaces=20,
        difficulty_level="Easy",
        language="es",
        available_slots=10,
    )
    assert activity.id is not None
    assert activity.available_slots > 0
    # Asociar metadata
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=ContentType.objects.get_for_model(Activities),
        object_id=activity.id,
        unit_price=1500,
    )
    assert metadata.id is not None
    assert metadata.supplier == supplier

@pytest.mark.django_db
def test_create_activity_with_no_slots(supplier, location):
    activity = Activities.objects.create(
        name="Kayak sin cupo",
        description="No hay cupos disponibles",
        location=location,
        date=date.today() + timedelta(days=2),
        start_time="10:00:00",
        duration_hours=2,
        include_guide=True,
        maximum_spaces=0,
        difficulty_level="Easy",
        language="es",
        available_slots=0,
    )
    assert activity.available_slots == 0

# --- TESTS DE AUTENTICACIÓN DE CLIENTE Y CAPTURA DE ACCESS TOKEN ---
from api.users.models import Users
from api.clients.models import Clients
from api.core.auth import gen_token

@pytest.mark.django_db
def test_client_login_and_token():
    # Crear usuario y cliente
    user = Users.objects.create_user(
        email="cliente@ejemplo.com",
        name="Cliente",
        last_name="Prueba",
        password="Testpass123",
        telephone="1234567890",
        born_date=date(1990, 1, 1),
        state="active"
    )
    client = Clients.objects.create(
        user=user,
        identity_document_type="Passport",
        identity_document="A1234567",
        state="active"
    )
    # Login vía API
    api_client = TestClient(ninja_api, urls_namespace=f"test-{uuid4()}")
    payload = {"email": "cliente@ejemplo.com", "password": "Testpass123"}
    response = api_client.post("/users/login", json=payload)
    if response.status_code != 200:
        print("DEBUG LOGIN TOKEN:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login exitoso"
    token = data["data"]["token"]  # Usar el token real devuelto por el login
    assert token is not None
    # Probar acceso a endpoint protegido
    response_me = api_client.get("/users/me", headers={"HTTP_AUTHORIZATION": f"Bearer {token}"})
    if response_me.status_code != 200:
        print("DEBUG ME:", response_me.status_code, response_me.content)
    assert response_me.status_code == 200
    user_data = response_me.json()
    assert user_data["email"] == "cliente@ejemplo.com"

@pytest.mark.django_db
def test_client_login_invalid_password():
    user = Users.objects.create_user(
        email="cliente2@ejemplo.com",
        name="Cliente2",
        last_name="Prueba2",
        password="Testpass123",
        telephone="1234567891",
        born_date=date(1991, 2, 2),
        state="active"
    )
    api_client = TestClient(ninja_api, urls_namespace=f"test-{uuid4()}")
    payload = {"email": "cliente2@ejemplo.com", "password": "ContraseñaIncorrecta"}
    response = api_client.post("/users/login", json=payload)
    if response.status_code != 401:
        print("DEBUG LOGIN INVALID:", response.status_code, response.content)
    assert response.status_code == 401
    data = response.json()
    if "message" not in data:
        print("DEBUG LOGIN INVALID JSON:", data)
    assert "message" in data and "Credenciales inválidas" in data["message"] 