# tests/test_transportation.py
import os
import sys
import django
from django.conf import settings

# Configurar Django antes de importar ninja
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

from ninja.testing import TestClient
from datetime import date, time, timedelta
from api.products.views_products import products_router
from api.products.models import Transportation, TransportationAvailability, ProductsMetadata
from django.contrib.contenttypes.models import ContentType
import pytest
import json

@pytest.fixture
def ninja_client():
    """Cliente de Ninja para testing"""
    return TestClient(products_router)

@pytest.fixture
def origin_location():
    """Crear ubicación de origen para testing"""
    from api.products.models import Location
    return Location.objects.create(
        country="Argentina",
        state="Buenos Aires",
        city="Buenos Aires"
    )

@pytest.fixture
def destination_location():
    """Crear ubicación de destino para testing"""
    from api.products.models import Location
    return Location.objects.create(
        country="Argentina",
        state="Río Negro",
        city="Bariloche"
    )

@pytest.fixture
def transportation_metadata(supplier, origin_location, destination_location):
    """Crear un transporte de prueba con su metadata"""
    # Crear el transporte
    transportation = Transportation.objects.create(
        origin=origin_location,
        destination=destination_location,
        type="bus",
        description="Servicio de bus directo Buenos Aires - Bariloche",
        notes="Incluye wifi y aire acondicionado",
        capacity=45
    )
    
    # Crear la metadata del producto
    content_type = ContentType.objects.get_for_model(Transportation)
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=transportation.id,
        precio_unitario=120.0
    )
    
    return metadata

@pytest.fixture
def transportation_with_availability(transportation_metadata):
    """Crear un transporte con disponibilidad para testing"""
    transportation = transportation_metadata.content
    
    # Crear disponibilidad
    availability = TransportationAvailability.objects.create(
        transportation=transportation,
        departure_date=date.today() + timedelta(days=5),
        departure_time=time(8, 0),  # 08:00
        arrival_date=date.today() + timedelta(days=5),
        arrival_time=time(20, 0),  # 20:00
        total_seats=45,
        reserved_seats=10,
        price=120.0,
        currency="USD",
        state="active"
    )
    
    return transportation, availability

@pytest.mark.django_db
def test_crear_transporte_simple_valido(ninja_client, supplier, origin_location, destination_location):
    """Test para crear un transporte válido usando el endpoint básico"""
    payload = {
        "tipo_producto": "transportation",
        "precio_unitario": 150,
        "supplier_id": supplier.id,
        "producto": {
            "origin_id": origin_location.id,
            "destination_id": destination_location.id,
            "type": "bus",
            "description": "Servicio de bus premium Buenos Aires - Bariloche",
            "notes": "Incluye wifi, aire acondicionado y servicio de catering",
            "capacity": 30
        }
    }
    
    print(f"Enviando payload: {json.dumps(payload, indent=2)}")
    response = ninja_client.post("/productos/crear/", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["tipo_producto"] == "transportation"
    assert data["producto"]["description"] == "Servicio de bus premium Buenos Aires - Bariloche"
    assert data["producto"]["capacity"] == 30
    assert data["precio_unitario"] == 150

@pytest.mark.django_db
def test_crear_transporte_completo_valido(ninja_client, supplier, origin_location, destination_location):
    """Test para crear un transporte completo con disponibilidades"""
    payload = {
        "precio_unitario": 120,
        "supplier_id": supplier.id,
        "origin_id": origin_location.id,
        "destination_id": destination_location.id,
        "type": "bus",
        "description": "Servicio de bus directo Buenos Aires - Bariloche",
        "notes": "Incluye wifi y aire acondicionado",
        "capacity": 45,
        "availabilities": [
            {
                "departure_date": str(date.today() + timedelta(days=5)),
                "departure_time": "08:00",
                "arrival_date": str(date.today() + timedelta(days=5)),
                "arrival_time": "20:00",
                "total_seats": 45,
                "reserved_seats": 0,
                "price": 120,
                "currency": "USD",
                "state": "active"
            },
            {
                "departure_date": str(date.today() + timedelta(days=6)),
                "departure_time": "08:00",
                "arrival_date": str(date.today() + timedelta(days=6)),
                "arrival_time": "20:00",
                "total_seats": 45,
                "reserved_seats": 5,
                "price": 120,
                "currency": "USD",
                "state": "active"
            }
        ]
    }
    
    print(f"Enviando payload completo: {json.dumps(payload, indent=2)}")
    response = ninja_client.post("/productos/transporte-completo/", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["tipo_producto"] == "transportation"
    assert data["producto"]["description"] == "Servicio de bus directo Buenos Aires - Bariloche"
    assert data["precio_unitario"] == 120
    
    # Verificar que se crearon las disponibilidades
    transportation = Transportation.objects.get(description="Servicio de bus directo Buenos Aires - Bariloche")
    assert transportation.availabilities.count() == 2
    
    # Verificar la primera disponibilidad
    availability1 = transportation.availabilities.get(departure_date=date.today() + timedelta(days=5))
    assert availability1.total_seats == 45
    assert availability1.reserved_seats == 0
    assert availability1.price == 120.0
    assert availability1.departure_time == time(8, 0)
    assert availability1.arrival_time == time(20, 0)
    
    # Verificar la segunda disponibilidad
    availability2 = transportation.availabilities.get(departure_date=date.today() + timedelta(days=6))
    assert availability2.total_seats == 45
    assert availability2.reserved_seats == 5
    assert availability2.price == 120.0

@pytest.mark.django_db
def test_crear_transporte_con_descripcion_vacia(ninja_client, supplier, origin_location, destination_location):
    """Test para validar error cuando la descripción está vacía"""
    payload = {
        "precio_unitario": 120,
        "supplier_id": supplier.id,
        "origin_id": origin_location.id,
        "destination_id": destination_location.id,
        "type": "bus",
        "description": "",
        "notes": "Incluye wifi y aire acondicionado",
        "capacity": 45
    }
    
    print(f"Enviando payload (descripción vacía): {json.dumps(payload, indent=2)}")
    response = ninja_client.post("/productos/transporte-completo/", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 422
    assert "description" in str(response.content) or "empty" in str(response.content).lower()

@pytest.mark.django_db
def test_crear_transporte_completo_con_disponibilidad_invalida(ninja_client, supplier, origin_location, destination_location):
    """Test para validar error cuando la disponibilidad tiene datos inválidos"""
    payload = {
        "precio_unitario": 120,
        "supplier_id": supplier.id,
        "origin_id": origin_location.id,
        "destination_id": destination_location.id,
        "type": "bus",
        "description": "Servicio de bus directo",
        "capacity": 45,
        "availabilities": [
            {
                "departure_date": str(date.today() + timedelta(days=5)),
                "departure_time": "08:00",
                "arrival_date": str(date.today() + timedelta(days=5)),
                "arrival_time": "07:00",  # Hora de llegada antes que salida
                "total_seats": 45,
                "reserved_seats": 50,  # Más reservados que total
                "price": 120,
                "currency": "USD"
            }
        ]
    }
    
    print(f"Enviando payload (disponibilidad inválida): {json.dumps(payload, indent=2)}")
    response = ninja_client.post("/productos/transporte-completo/", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 422
    # Debería fallar por hora de llegada anterior a salida o asientos reservados > total

@pytest.mark.django_db
def test_crear_transporte_completo_sin_disponibilidades(ninja_client, supplier, origin_location, destination_location):
    """Test para crear un transporte completo sin disponibilidades"""
    payload = {
        "precio_unitario": 120,
        "supplier_id": supplier.id,
        "origin_id": origin_location.id,
        "destination_id": destination_location.id,
        "type": "van",
        "description": "Servicio de van privado",
        "notes": "Servicio exclusivo",
        "capacity": 8,
        "availabilities": []
    }
    
    print(f"Enviando payload (sin disponibilidades): {json.dumps(payload, indent=2)}")
    response = ninja_client.post("/productos/transporte-completo/", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["tipo_producto"] == "transportation"
    assert data["producto"]["type"] == "van"
    assert data["producto"]["capacity"] == 8
    
    # Verificar que no se crearon disponibilidades
    transportation = Transportation.objects.get(description="Servicio de van privado")
    assert transportation.availabilities.count() == 0

@pytest.mark.django_db
def test_crear_disponibilidad_para_transporte(ninja_client, transportation_metadata):
    """Test para crear una disponibilidad para un transporte existente"""
    payload = {
        "departure_date": str(date.today() + timedelta(days=7)),
        "departure_time": "09:00",
        "arrival_date": str(date.today() + timedelta(days=7)),
        "arrival_time": "21:00",
        "total_seats": 45,
        "reserved_seats": 3,
        "price": 120.0,
        "currency": "USD",
        "state": "active"
    }
    
    print(f"Enviando payload disponibilidad: {json.dumps(payload, indent=2)}")
    response = ninja_client.post(f"/productos/{transportation_metadata.id}/transportation-availability/", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["transportation_id"] == transportation_metadata.content.id
    assert data["total_seats"] == 45
    assert data["reserved_seats"] == 3
    assert data["price"] == 120.0
    assert data["departure_time"] == "09:00:00"
    assert data["arrival_time"] == "21:00:00"

@pytest.mark.django_db
def test_listar_disponibilidades_transporte(ninja_client, transportation_with_availability):
    """Test para listar las disponibilidades de un transporte"""
    transportation, availability = transportation_with_availability
    # Usar la relación directa en lugar de content
    metadata = ProductsMetadata.objects.filter(
        content_type_id__model='transportation',
        object_id=transportation.id
    ).first()
    
    print(f"Consultando disponibilidades para transporte ID: {metadata.id}")
    response = ninja_client.get(f"/productos/{metadata.id}/transportation-availability/")
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    
    availability_data = data[0]
    assert availability_data["transportation_id"] == transportation.id
    assert availability_data["total_seats"] == 45
    assert availability_data["reserved_seats"] == 10
    assert availability_data["price"] == 120.0

@pytest.mark.django_db
def test_actualizar_disponibilidad_transporte(ninja_client, transportation_with_availability):
    """Test para actualizar una disponibilidad de transporte"""
    transportation, availability = transportation_with_availability
    
    payload = {
        "total_seats": 50,
        "reserved_seats": 15,
        "price": 130.0,
        "currency": "ARS"
    }
    
    print(f"Actualizando disponibilidad ID: {availability.id}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    response = ninja_client.patch(f"/productos/transportation-availability/{availability.id}/", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_seats"] == 50
    assert data["reserved_seats"] == 15
    assert data["price"] == 130.0
    assert data["currency"] == "ARS"
    
    # Verificar que se actualizó en la base de datos
    availability.refresh_from_db()
    assert availability.total_seats == 50
    assert availability.reserved_seats == 15
    assert availability.price == 130.0

@pytest.mark.django_db
def test_eliminar_disponibilidad_transporte(ninja_client, transportation_with_availability):
    """Test para eliminar una disponibilidad de transporte"""
    transportation, availability = transportation_with_availability
    
    print(f"Eliminando disponibilidad ID: {availability.id}")
    response = ninja_client.delete(f"/productos/transportation-availability/{availability.id}/")
    print(f"Status code: {response.status_code}")
    
    assert response.status_code == 204
    
    # Verificar que se eliminó de la base de datos
    with pytest.raises(TransportationAvailability.DoesNotExist):
        availability.refresh_from_db()

@pytest.mark.django_db
def test_obtener_transporte_por_id(ninja_client, transportation_metadata):
    """Test para obtener un transporte por su ID"""
    print(f"Consultando transporte ID: {transportation_metadata.id}")
    response = ninja_client.get(f"/productos/{transportation_metadata.id}/")
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["tipo_producto"] == "transportation"
    assert data["producto"]["description"] == "Servicio de bus directo Buenos Aires - Bariloche"
    assert data["producto"]["capacity"] == 45
    assert data["producto"]["type"] == "bus"

@pytest.mark.django_db
def test_actualizar_transporte(ninja_client, transportation_metadata):
    """Test para actualizar un transporte"""
    # El endpoint espera un esquema específico ProductsMetadataUpdateTransportation
    payload = {
        "precio_unitario": 140.0,
        "producto": {
            "description": "Transporte actualizado - Bus de lujo con WiFi"
        }
    }

    print(f"Actualizando transporte ID: {transportation_metadata.id}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    response = ninja_client.patch(f"/productos/{transportation_metadata.id}/", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")

    assert response.status_code == 200
    data = response.json()
    assert data["precio_unitario"] == 140.0
    assert data["producto"]["description"] == "Transporte actualizado - Bus de lujo con WiFi"

@pytest.mark.django_db
def test_inactivar_transporte(ninja_client, transportation_metadata):
    """Test para inactivar un transporte"""
    print(f"Inactivando transporte ID: {transportation_metadata.id}")
    response = ninja_client.delete(f"/productos/{transportation_metadata.id}/")
    print(f"Status code: {response.status_code}")
    
    assert response.status_code == 204
    
    # Verificar que se inactivó en la base de datos
    transportation_metadata.refresh_from_db()
    assert transportation_metadata.is_active == False
    assert transportation_metadata.deleted_at is not None
    
    transportation = transportation_metadata.content
    assert transportation.is_active == False

@pytest.mark.django_db
def test_obtener_transporte_inexistente(ninja_client):
    """Test para obtener un transporte que no existe"""
    print("Consultando transporte inexistente ID: 99999")
    response = ninja_client.get("/productos/99999/")
    print(f"Status code: {response.status_code}")
    
    assert response.status_code == 404

@pytest.mark.django_db
def test_crear_disponibilidad_para_producto_no_transporte(ninja_client, supplier, origin_location, destination_location):
    """Test para validar error al crear disponibilidad para un producto que no es transporte"""
    # Crear una actividad en lugar de transporte
    from api.products.models import Activities
    activity = Activities.objects.create(
        name="Test Activity",
        description="Test Description",
        location=origin_location,
        date=date.today() + timedelta(days=10),
        start_time=time(9, 0),
        duration_hours=2,
        include_guide=True,
        maximum_spaces=10,
        difficulty_level="Easy",
        language="Español",
        available_slots=10
    )
    
    content_type = ContentType.objects.get_for_model(Activities)
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=activity.id,
        precio_unitario=50.0
    )
    
    payload = {
        "departure_date": str(date.today() + timedelta(days=5)),
        "departure_time": "08:00",
        "arrival_date": str(date.today() + timedelta(days=5)),
        "arrival_time": "20:00",
        "total_seats": 45,
        "reserved_seats": 0,
        "price": 120.0,
        "currency": "USD"
    }
    
    print(f"Intentando crear disponibilidad de transporte para actividad ID: {metadata.id}")
    response = ninja_client.post(f"/productos/{metadata.id}/transportation-availability/", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 400
    assert "not a transportation" in str(response.content).lower()

@pytest.mark.django_db
def test_crear_disponibilidad_con_fecha_pasada(ninja_client, transportation_metadata):
    """Test para validar error cuando la fecha de salida es en el pasado"""
    payload = {
        "departure_date": str(date.today() - timedelta(days=1)),
        "departure_time": "08:00",
        "arrival_date": str(date.today() - timedelta(days=1)),
        "arrival_time": "20:00",
        "total_seats": 45,
        "reserved_seats": 0,
        "price": 120.0,
        "currency": "USD"
    }
    
    print(f"Enviando disponibilidad con fecha pasada: {json.dumps(payload, indent=2)}")
    response = ninja_client.post(f"/productos/{transportation_metadata.id}/transportation-availability/", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 422
    assert "past" in str(response.content).lower()

@pytest.mark.django_db
def test_crear_disponibilidad_con_asientos_invalidos(ninja_client, transportation_metadata):
    """Test para validar error cuando los asientos reservados superan el total"""
    payload = {
        "departure_date": str(date.today() + timedelta(days=5)),
        "departure_time": "08:00",
        "arrival_date": str(date.today() + timedelta(days=5)),
        "arrival_time": "20:00",
        "total_seats": 45,
        "reserved_seats": 50,  # Más reservados que total
        "price": 120.0,
        "currency": "USD"
    }
    
    print(f"Enviando disponibilidad con asientos inválidos: {json.dumps(payload, indent=2)}")
    response = ninja_client.post(f"/productos/{transportation_metadata.id}/transportation-availability/", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 422
    assert "exceed" in str(response.content).lower()

@pytest.mark.django_db
def test_diferentes_tipos_transporte(ninja_client, supplier, origin_location, destination_location):
    """Test para crear transportes con diferentes tipos"""
    tipos_transporte = ["bus", "van", "car", "shuttle", "train", "other"]
    
    for tipo in tipos_transporte:
        payload = {
            "precio_unitario": 100,
            "supplier_id": supplier.id,
            "origin_id": origin_location.id,
            "destination_id": destination_location.id,
            "type": tipo,
            "description": f"Servicio de {tipo}",
            "capacity": 20
        }
        
        print(f"Creando transporte tipo: {tipo}")
        response = ninja_client.post("/productos/transporte-completo/", json=payload)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["producto"]["type"] == tipo

@pytest.mark.django_db
def test_capacidad_transporte_limites(ninja_client, supplier, origin_location, destination_location):
    """Test para validar los límites de capacidad del transporte"""
    # Test con capacidad mínima (1)
    payload_min = {
        "precio_unitario": 100,
        "supplier_id": supplier.id,
        "origin_id": origin_location.id,
        "destination_id": destination_location.id,
        "type": "car",
        "description": "Auto privado",
        "capacity": 1
    }
    
    print("Creando transporte con capacidad mínima")
    response = ninja_client.post("/productos/transporte-completo/", json=payload_min)
    assert response.status_code == 200
    
    # Test con capacidad máxima (100)
    payload_max = {
        "precio_unitario": 100,
        "supplier_id": supplier.id,
        "origin_id": origin_location.id,
        "destination_id": destination_location.id,
        "type": "bus",
        "description": "Bus grande",
        "capacity": 100
    }
    
    print("Creando transporte con capacidad máxima")
    response = ninja_client.post("/productos/transporte-completo/", json=payload_max)
    assert response.status_code == 200
    
    # Test con capacidad inválida (0)
    payload_invalid = {
        "precio_unitario": 100,
        "supplier_id": supplier.id,
        "origin_id": origin_location.id,
        "destination_id": destination_location.id,
        "type": "bus",
        "description": "Bus inválido",
        "capacity": 0
    }
    
    print("Creando transporte con capacidad inválida")
    response = ninja_client.post("/productos/transporte-completo/", json=payload_invalid)
    assert response.status_code == 422 