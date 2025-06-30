import pytest
from datetime import date, timedelta, time
from api.products.models import Activities, Flights, Lodgment, Room
import random

@pytest.mark.django_db
def test_crear_actividad_valida_completa(ninja_client, supplier, location):
    """Test completo para crear una actividad con todos los campos"""
    payload = {
        "product_type": "activity",
        "unit_price": 150.0,
        "supplier_id": supplier.id,
        "product": {
            "name": "Rafting en el Río Manso",
            "description": "Aventura de rafting de nivel intermedio en el Río Manso, incluye equipo y guía profesional.",
            "location_id": location.id,
            "date": str(date.today() + timedelta(days=10)),
            "start_time": "08:30:00",
            "duration_hours": 6,
            "include_guide": True,
            "maximum_spaces": 20,
            "difficulty_level": "Medium",
            "language": "Español",
            "available_slots": 20
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 200:
        print("\nRespuesta de error ACTIVITY COMPLETA:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "activity"
    assert data["unit_price"] == 150.0
    assert "id" in data
    assert "product" in data
    prod = data["product"]
    assert prod["name"] == payload["product"]["name"]
    assert prod["description"] == payload["product"]["description"]
    assert prod["duration_hours"] == payload["product"]["duration_hours"]
    assert prod["include_guide"] is True
    assert prod["maximum_spaces"] == 20
    assert prod["difficulty_level"] == "Medium"
    assert prod["language"] == "Español"
    assert prod["available_slots"] == 20
    assert "location" in prod
    assert prod["location"]["city"] == location.city
    # Validar existencia en la base
    assert Activities.objects.filter(name="Rafting en el Río Manso").exists()

@pytest.mark.django_db
def test_crear_actividad_valida_obligatorios(ninja_client, supplier, location):
    """Test para crear una actividad solo con los campos obligatorios"""
    payload = {
        "product_type": "activity",
        "unit_price": 100.0,
        "supplier_id": supplier.id,
        "product": {
            "name": "Trekking Cerro Otto",
            "description": "Caminata guiada al Cerro Otto",
            "location_id": location.id,
            "date": str(date.today() + timedelta(days=5)),
            "start_time": "10:00:00",
            "duration_hours": 3,
            "include_guide": False,
            "maximum_spaces": 10,
            "difficulty_level": "Easy",
            "language": "Español",
            "available_slots": 10
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 200:
        print("\nRespuesta de error ACTIVITY OBLIGATORIOS:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "activity"
    assert data["unit_price"] == 100.0
    assert data["product"]["name"] == "Trekking Cerro Otto"
    assert Activities.objects.filter(name="Trekking Cerro Otto").exists()

@pytest.mark.django_db
@pytest.mark.parametrize("campo", [
    "name", "description", "location_id", "date", "start_time", "duration_hours", "include_guide", "maximum_spaces", "difficulty_level", "language", "available_slots"
])
def test_crear_actividad_faltante_obligatorio(ninja_client, supplier, location, campo):
    """Test de error: falta un campo obligatorio"""
    base = {
        "name": "Kayak en el Lago",
        "description": "Remada guiada en lago",
        "location_id": location.id,
        "date": str(date.today() + timedelta(days=7)),
        "start_time": "11:00:00",
        "duration_hours": 2,
        "include_guide": True,
        "maximum_spaces": 8,
        "difficulty_level": "Easy",
        "language": "Español",
        "available_slots": 8
    }
    base.pop(campo)
    payload = {
        "product_type": "activity",
        "unit_price": 90.0,
        "supplier_id": supplier.id,
        "product": base
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 422:
        print(f"\nRespuesta de error ACTIVITY FALTANTE {campo}:", response.status_code, response.content)
    assert response.status_code == 422
    assert campo in response.content.decode()

@pytest.mark.django_db
@pytest.mark.parametrize("campo,valor", [
    ("duration_hours", -1),
    ("maximum_spaces", -5),
    ("available_slots", -2),
    ("date", str(date.today() - timedelta(days=1))),
    ("difficulty_level", "SuperHard"),
])
def test_crear_actividad_invalida_valor(ninja_client, supplier, location, campo, valor):
    """Test de error: valor inválido en campo"""
    base = {
        "name": "Canopy",
        "description": "Tirolesa en bosque",
        "location_id": location.id,
        "date": str(date.today() + timedelta(days=3)),
        "start_time": "12:00:00",
        "duration_hours": 2,
        "include_guide": True,
        "maximum_spaces": 10,
        "difficulty_level": "Medium",
        "language": "Español",
        "available_slots": 10
    }
    base[campo] = valor
    payload = {
        "product_type": "activity",
        "unit_price": 120.0,
        "supplier_id": supplier.id,
        "product": base
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 422:
        print(f"\nRespuesta de error ACTIVITY INVALIDA {campo}:", response.status_code, response.content)
    assert response.status_code == 422
    assert campo in response.content.decode()

@pytest.mark.django_db
def test_crear_actividad_invalida_logica(ninja_client, supplier, location):
    """Test de error: fecha en el pasado y asientos negativos"""
    payload = {
        "product_type": "activity",
        "unit_price": 120.0,
        "supplier_id": supplier.id,
        "product": {
            "name": "Caminata al Lago",
            "description": "Caminata guiada al lago escondido",
            "location_id": location.id,
            "date": str(date.today() - timedelta(days=1)),
            "start_time": "09:00:00",
            "duration_hours": 4,
            "include_guide": True,
            "maximum_spaces": -5,
            "difficulty_level": "Easy",
            "language": "Español",
            "available_slots": 15
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 422:
        print("\nRespuesta de error ACTIVITY LOGICA:", response.status_code, response.content)
    assert response.status_code == 422
    assert "date" in response.content.decode() or "maximum_spaces" in response.content.decode()

@pytest.mark.django_db
def test_crear_actividad_proveedor_inexistente(ninja_client, location):
    """Test para crear una actividad con proveedor inexistente"""
    payload = {
        "product_type": "activity",
        "unit_price": 120.0,
        "supplier_id": 99999,  # ID que no existe
        "product": {
            "name": "Caminata al Lago",
            "description": "Caminata guiada al lago escondido",
            "location_id": location.id,
            "date": str(date.today() + timedelta(days=5)),
            "start_time": "09:00:00",
            "duration_hours": 4,
            "include_guide": True,
            "maximum_spaces": 15,
            "difficulty_level": "Easy",
            "language": "Español",
            "available_slots": 15
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    assert response.status_code == 404

@pytest.mark.django_db
def test_crear_flight_valido_completo(ninja_client, supplier, location):
    """Test completo para crear un vuelo con todos los campos"""
    payload = {
        "product_type": "flight",
        "unit_price": 350.0,
        "supplier_id": supplier.id,
        "product": {
            "airline": "Aerolineas Argentinas",
            "flight_number": "AR1234",
            "origin_id": location.id,
            "destination_id": location.id,
            "departure_date": str(date.today() + timedelta(days=15)),
            "departure_time": "14:45:00",
            "arrival_date": str(date.today() + timedelta(days=15)),
            "arrival_time": "17:30:00",
            "duration_hours": 3,
            "class_flight": "Economy",
            "available_seats": 120,
            "luggage_info": "1 valija 23kg + 1 bolso de mano",
            "aircraft_type": "Boeing 737",
            "terminal": "A",
            "gate": "12",
            "notes": "Embarque prioritario"
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 200:
        print("\nRespuesta de error FLIGHT COMPLETO:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "flight"
    assert data["unit_price"] == 350.0
    assert "id" in data
    assert "product" in data
    prod = data["product"]
    assert prod["airline"] == payload["product"]["airline"]
    assert prod["flight_number"] == payload["product"]["flight_number"]
    assert prod["origin"]["city"] == location.city
    assert prod["destination"]["city"] == location.city
    assert prod["departure_date"] == payload["product"]["departure_date"]
    assert prod["departure_time"] == payload["product"]["departure_time"]
    assert prod["arrival_date"] == payload["product"]["arrival_date"]
    assert prod["arrival_time"] == payload["product"]["arrival_time"]
    assert prod["duration_hours"] == 3
    assert prod["class_flight"] == "Economy"
    assert prod["available_seats"] == 120
    assert prod["luggage_info"] == "1 valija 23kg + 1 bolso de mano"
    assert prod["aircraft_type"] == "Boeing 737"
    assert prod["terminal"] == "A"
    assert prod["gate"] == "12"
    assert prod["notes"] == "Embarque prioritario"
    # Validar existencia en la base
    assert Flights.objects.filter(flight_number="AR1234").exists()

@pytest.mark.django_db
def test_crear_flight_valido_obligatorios(ninja_client, supplier, location):
    """Test para crear un vuelo solo con los campos obligatorios"""
    payload = {
        "product_type": "flight",
        "unit_price": 200.0,
        "supplier_id": supplier.id,
        "product": {
            "airline": "JetSmart",
            "flight_number": "JS5678",
            "origin_id": location.id,
            "destination_id": location.id,
            "departure_date": str(date.today() + timedelta(days=10)),
            "departure_time": "09:00:00",
            "arrival_date": str(date.today() + timedelta(days=10)),
            "arrival_time": "11:00:00",
            "duration_hours": 2,
            "class_flight": "Economy",
            "available_seats": 80,
            "luggage_info": "Solo bolso de mano",
            "aircraft_type": "Airbus A320"
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 200:
        print("\nRespuesta de error FLIGHT OBLIGATORIOS:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "flight"
    assert data["unit_price"] == 200.0
    assert data["product"]["flight_number"] == "JS5678"
    assert Flights.objects.filter(flight_number="JS5678").exists()

@pytest.mark.django_db
@pytest.mark.parametrize("campo", [
    "airline", "flight_number", "origin_id", "destination_id", "departure_date", "departure_time", "arrival_date", "arrival_time", "duration_hours", "class_flight", "available_seats", "luggage_info", "aircraft_type"
])
def test_crear_flight_faltante_obligatorio(ninja_client, supplier, location, campo):
    """Test de error: falta un campo obligatorio en vuelo"""
    base = {
        "airline": "LATAM",
        "flight_number": "LA9999",
        "origin_id": location.id,
        "destination_id": location.id,
        "departure_date": str(date.today() + timedelta(days=8)),
        "departure_time": "13:00:00",
        "arrival_date": str(date.today() + timedelta(days=8)),
        "arrival_time": "15:00:00",
        "duration_hours": 2,
        "class_flight": "Economy",
        "available_seats": 100,
        "luggage_info": "1 valija",
        "aircraft_type": "Boeing 777"
    }
    base.pop(campo)
    payload = {
        "product_type": "flight",
        "unit_price": 180.0,
        "supplier_id": supplier.id,
        "product": base
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 422:
        print(f"\nRespuesta de error FLIGHT FALTANTE {campo}:", response.status_code, response.content)
    assert response.status_code == 422
    assert campo in response.content.decode()

@pytest.mark.django_db
@pytest.mark.parametrize("campo,valor", [
    ("duration_hours", -1),
    ("available_seats", -5),
    ("departure_date", str(date.today() - timedelta(days=1))),
    ("arrival_date", str(date.today() - timedelta(days=2))),
    ("class_flight", "SuperLuxury"),
])
def test_crear_flight_invalida_valor(ninja_client, supplier, location, campo, valor):
    """Test de error: valor inválido en campo de vuelo"""
    base = {
        "airline": "Andes",
        "flight_number": "AN123",
        "origin_id": location.id,
        "destination_id": location.id,
        "departure_date": str(date.today() + timedelta(days=3)),
        "departure_time": "12:00:00",
        "arrival_date": str(date.today() + timedelta(days=3)),
        "arrival_time": "14:00:00",
        "duration_hours": 2,
        "class_flight": "Economy",
        "available_seats": 50,
        "luggage_info": "1 bolso",
        "aircraft_type": "Embraer 190"
    }
    base[campo] = valor
    payload = {
        "product_type": "flight",
        "unit_price": 120.0,
        "supplier_id": supplier.id,
        "product": base
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 422:
        print(f"\nRespuesta de error FLIGHT INVALIDA {campo}:", response.status_code, response.content)
    assert response.status_code == 422
    content = response.content.decode()
    if campo == "departure_date":
        assert "Departure date cannot be in the past." in content
    elif campo == "arrival_date":
        assert "Arrival date must be after departure date." in content
    else:
        assert campo in content

@pytest.mark.django_db
def test_crear_flight_invalida_logica(ninja_client, supplier, location):
    """Test de error: llegada antes que salida y asientos negativos"""
    payload = {
        "product_type": "flight",
        "unit_price": 120.0,
        "supplier_id": supplier.id,
        "product": {
            "airline": "Sky",
            "flight_number": "SKY001",
            "origin_id": location.id,
            "destination_id": location.id,
            "departure_date": str(date.today() + timedelta(days=5)),
            "departure_time": "10:00:00",
            "arrival_date": str(date.today() + timedelta(days=4)),  # llegada antes
            "arrival_time": "09:00:00",
            "duration_hours": 2,
            "class_flight": "Economy",
            "available_seats": -10,
            "luggage_info": "1 bolso",
            "aircraft_type": "Boeing 737"
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 422:
        print("\nRespuesta de error FLIGHT LOGICA:", response.status_code, response.content)
    assert response.status_code == 422
    assert "arrival_date" in response.content.decode() or "available_seats" in response.content.decode()

@pytest.mark.django_db
def test_crear_lodgment_valido_completo(ninja_client, supplier, location):
    """Test completo para crear un alojamiento con datos realistas de producción"""
    payload = {
        "product_type": "lodgment",
        "unit_price": 800.0,
        "supplier_id": supplier.id,
        "product": {
            "name": "Hotel Patagonia Sur",
            "description": "Hotel 4 estrellas con vista al lago y spa.",
            "location_id": location.id,
            "type": "hotel",
            "max_guests": 4,
            "contact_phone": "+54 294 5555555",
            "contact_email": "info@patagoniasur.com",
            "amenities": ["wifi", "spa", "pileta", "desayuno"],
            "date_checkin": str(date.today() + timedelta(days=30)),
            "date_checkout": str(date.today() + timedelta(days=35))
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 200:
        print("\nRespuesta de error LODGMENT:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "lodgment"
    assert data["unit_price"] == 800.0
    assert "id" in data
    assert "product" in data
    prod = data["product"]
    assert prod["name"] == payload["product"]["name"]
    assert prod["description"] == payload["product"]["description"]
    assert prod["location"]["city"] == location.city
    assert prod["type"] == "hotel"
    assert prod["max_guests"] == 4
    assert prod["contact_phone"] == "+54 294 5555555"
    assert prod["contact_email"] == "info@patagoniasur.com"
    assert set(prod["amenities"]) == set(["wifi", "spa", "pileta", "desayuno"])
    assert prod["date_checkin"] == payload["product"]["date_checkin"]
    assert prod["date_checkout"] == payload["product"]["date_checkout"]

@pytest.mark.django_db
def test_crear_transportation_valido_completo(ninja_client, supplier, location):
    """Test completo para crear un transporte con datos realistas de producción"""
    payload = {
        "product_type": "transportation",
        "unit_price": 250.0,
        "supplier_id": supplier.id,
        "product": {
            "origin_id": location.id,
            "destination_id": location.id,
            "type": "bus",
            "description": "Servicio de bus Bariloche - Villa La Angostura, con aire acondicionado y wifi.",
            "notes": "Parada intermedia en Dina Huapi.",
            "capacity": 45
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 200:
        print("\nRespuesta de error TRANSPORTATION:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "transportation"
    assert data["unit_price"] == 250.0
    assert "id" in data
    assert "product" in data
    prod = data["product"]
    assert prod["origin"]["city"] == location.city
    assert prod["destination"]["city"] == location.city
    assert prod["type"] == "bus"
    assert prod["description"] == "Servicio de bus Bariloche - Villa La Angostura, con aire acondicionado y wifi."
    assert prod["notes"] == "Parada intermedia en Dina Huapi."
    assert prod["capacity"] == 45

@pytest.mark.django_db
def test_crear_lodgment_completo_exitoso(ninja_client, supplier, location):
    """Test exitoso de creación completa de alojamiento con habitaciones y disponibilidades"""
    today = date.today()
    payload = {
        "data": {
            "name": "Hotel Patagonia Sur",
            "description": "Hotel 4 estrellas con vista al lago y spa.",
            "location_id": location.id,
            "type": "hotel",
            "max_guests": 10,
            "contact_phone": "+54 294 5555555",
            "contact_email": "info@patagoniasur.com",
            "amenities": ["wifi", "spa", "pileta", "desayuno"],
            "date_checkin": str(today + timedelta(days=10)),
            "date_checkout": str(today + timedelta(days=15)),
            "rooms": [
                {
                    "room_type": "double",
                    "name": "Doble Superior",
                    "description": "Habitación doble con vista al lago",
                    "capacity": 2,
                    "has_private_bathroom": True,
                    "has_balcony": True,
                    "has_air_conditioning": True,
                    "has_wifi": True,
                    "base_price_per_night": 200.0,
                    "currency": "USD",
                    "availabilities": [
                        {
                            "start_date": str(today + timedelta(days=10)),
                            "end_date": str(today + timedelta(days=12)),
                            "available_quantity": 3,
                            "price_override": 180.0,
                            "currency": "USD",
                            "is_blocked": False,
                            "minimum_stay": 2
                        }
                    ]
                },
                {
                    "room_type": "suite",
                    "name": "Suite Familiar",
                    "description": "Suite para 4 personas, ideal familias",
                    "capacity": 4,
                    "has_private_bathroom": True,
                    "has_balcony": False,
                    "has_air_conditioning": True,
                    "has_wifi": True,
                    "base_price_per_night": 350.0,
                    "currency": "USD",
                    "availabilities": [
                        {
                            "start_date": str(today + timedelta(days=11)),
                            "end_date": str(today + timedelta(days=15)),
                            "available_quantity": 2,
                            "price_override": 320.0,
                            "currency": "USD",
                            "is_blocked": False,
                            "minimum_stay": 3
                        }
                    ]
                }
            ]
        },
        "metadata": {
            "supplier_id": supplier.id,
            "unit_price": 1200.0
        }
    }
    response = ninja_client.post("/products/lodgment-complete/", json=payload)
    if response.status_code != 200:
        print("\nRespuesta de error LODGMENT COMPLETO:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "lodgment"
    assert data["unit_price"] == 1200.0
    assert "id" in data
    prod = data["product"]
    assert prod["name"] == payload["data"]["name"]
    assert prod["type"] == payload["data"]["type"]
    assert prod["max_guests"] == payload["data"]["max_guests"]
    assert prod["contact_email"] == payload["data"]["contact_email"]
    assert set(prod["amenities"]) == set(payload["data"]["amenities"])
    # Validar habitaciones
    assert len(prod["rooms"]) == 2
    nombres = [r["name"] for r in prod["rooms"]]
    assert "Doble Superior" in nombres and "Suite Familiar" in nombres
    # Validar existencia en la base
    assert Lodgment.objects.filter(name="Hotel Patagonia Sur").exists()
    assert Room.objects.filter(name="Doble Superior").exists()
    assert Room.objects.filter(name="Suite Familiar").exists()

@pytest.mark.django_db
@pytest.mark.parametrize("campo", [
    "name", "location_id", "type", "max_guests", "date_checkin", "date_checkout", "rooms"
])
def test_lodgment_completo_faltante_obligatorio(ninja_client, supplier, location, campo):
    """Test de error: falta un campo obligatorio en data"""
    today = date.today()
    base = {
        "name": "Hotel Test",
        "description": "Desc",
        "location_id": location.id,
        "type": "hotel",
        "max_guests": 5,
        "contact_phone": "+54 294 5555555",
        "contact_email": "info@hotel.com",
        "amenities": ["wifi"],
        "date_checkin": str(today + timedelta(days=10)),
        "date_checkout": str(today + timedelta(days=12)),
        "rooms": [
            {
                "room_type": "double",
                "capacity": 2,
                "base_price_per_night": 100.0,
                "currency": "USD",
                "availabilities": []
            }
        ]
    }
    base.pop(campo)
    payload = {
        "data": base,
        "metadata": {"supplier_id": supplier.id, "unit_price": 500.0}
    }
    response = ninja_client.post("/products/lodgment-complete/", json=payload)
    assert response.status_code == 422
    assert campo in response.content.decode()

@pytest.mark.django_db
def test_lodgment_completo_fecha_invalida(ninja_client, supplier, location):
    """Test de error: fecha de checkin en el pasado"""
    today = date.today()
    payload = {
        "data": {
            "name": "Hotel Test",
            "description": "Desc",
            "location_id": location.id,
            "type": "hotel",
            "max_guests": 5,
            "contact_phone": "+54 294 5555555",
            "contact_email": "info@hotel.com",
            "amenities": ["wifi"],
            "date_checkin": str(today - timedelta(days=1)),
            "date_checkout": str(today + timedelta(days=2)),
            "rooms": [
                {
                    "room_type": "double",
                    "capacity": 2,
                    "base_price_per_night": 100.0,
                    "currency": "USD",
                    "availabilities": []
                }
            ]
        },
        "metadata": {"supplier_id": supplier.id, "unit_price": 500.0}
    }
    response = ninja_client.post("/products/lodgment-complete/", json=payload)
    assert response.status_code == 422
    assert "checkin" in response.content.decode() or "Check-in" in response.content.decode()

@pytest.mark.django_db
def test_lodgment_completo_cantidad_negativa(ninja_client, supplier, location):
    """Test de error: cantidad negativa en disponibilidad de habitación"""
    today = date.today()
    payload = {
        "data": {
            "name": "Hotel Test",
            "description": "Desc",
            "location_id": location.id,
            "type": "hotel",
            "max_guests": 5,
            "contact_phone": "+54 294 5555555",
            "contact_email": "info@hotel.com",
            "amenities": ["wifi"],
            "date_checkin": str(today + timedelta(days=1)),
            "date_checkout": str(today + timedelta(days=3)),
            "rooms": [
                {
                    "room_type": "double",
                    "capacity": 2,
                    "base_price_per_night": 100.0,
                    "currency": "USD",
                    "availabilities": [
                        {
                            "start_date": str(today + timedelta(days=1)),
                            "end_date": str(today + timedelta(days=2)),
                            "available_quantity": -1,
                            "price_override": 90.0,
                            "currency": "USD",
                            "is_blocked": False,
                            "minimum_stay": 1
                        }
                    ]
                }
            ]
        },
        "metadata": {"supplier_id": supplier.id, "unit_price": 500.0}
    }
    response = ninja_client.post("/products/lodgment-complete/", json=payload)
    assert response.status_code == 422
    assert "available_quantity" in response.content.decode() or "mayor o igual a 0" in response.content.decode()

@pytest.mark.django_db
def test_crear_actividad_completa_exitoso(ninja_client, supplier, location):
    """Test exitoso de creación completa de actividad con disponibilidades"""
    today = date.today()
    payload = {
        "data": {
            "name": "Excursión al Cerro Tronador",
            "description": "Trekking de día completo con guía y refrigerio.",
            "location_id": location.id,
            "date": str(today + timedelta(days=7)),
            "start_time": "07:00:00",
            "duration_hours": 10,
            "include_guide": True,
            "maximum_spaces": 20,
            "difficulty_level": "Hard",
            "language": "Español",
            "available_slots": 20,
            "availabilities": [
                {
                    "event_date": str(today + timedelta(days=7)),
                    "start_time": "07:00:00",
                    "total_seats": 20,
                    "reserved_seats": 0,
                    "price": 250.0,
                    "currency": "USD",
                    "state": "active"
                },
                {
                    "event_date": str(today + timedelta(days=8)),
                    "start_time": "07:00:00",
                    "total_seats": 20,
                    "reserved_seats": 2,
                    "price": 250.0,
                    "currency": "USD",
                    "state": "active"
                }
            ]
        },
        "metadata": {
            "supplier_id": supplier.id,
            "unit_price": 250.0,
            "currency": "USD"
        }
    }
    response = ninja_client.post("/products/activity-complete/", json=payload)
    if response.status_code != 200:
        print("\nRespuesta de error ACTIVITY COMPLETA:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "activity"
    assert data["unit_price"] == 250.0
    assert "id" in data
    prod = data["product"]
    assert prod["name"] == payload["data"]["name"]
    assert prod["description"] == payload["data"]["description"]
    assert prod["duration_hours"] == 10
    assert prod["include_guide"] is True
    assert prod["maximum_spaces"] == 20
    assert prod["difficulty_level"] == "Hard"
    assert prod["language"] == "Español"
    assert prod["available_slots"] == 20
    assert prod["location"]["city"] == location.city
    # Validar existencia en la base
    assert Activities.objects.filter(name="Excursión al Cerro Tronador").exists()

@pytest.mark.django_db
@pytest.mark.parametrize("campo", [
    "name", "description", "location_id", "date", "start_time", "duration_hours", "include_guide", "maximum_spaces", "difficulty_level", "language", "available_slots"
])
def test_crear_actividad_completa_faltante_obligatorio(ninja_client, supplier, location, campo):
    today = date.today()
    base = {
        "name": "Excursión Test",
        "description": "Desc",
        "location_id": location.id,
        "date": str(today + timedelta(days=5)),
        "start_time": "08:00:00",
        "duration_hours": 5,
        "include_guide": True,
        "maximum_spaces": 10,
        "difficulty_level": "Medium",
        "language": "Español",
        "available_slots": 10,
        "availabilities": []
    }
    base.pop(campo)
    payload = {
        "data": base,
        "metadata": {"supplier_id": supplier.id, "unit_price": 100.0, "currency": "USD"}
    }
    response = ninja_client.post("/products/activity-complete/", json=payload)
    assert response.status_code == 422
    assert campo in response.content.decode()

@pytest.mark.django_db
def test_crear_actividad_completa_fecha_invalida(ninja_client, supplier, location):
    today = date.today()
    payload = {
        "data": {
            "name": "Excursión Test",
            "description": "Desc",
            "location_id": location.id,
            "date": str(today - timedelta(days=1)),
            "start_time": "08:00:00",
            "duration_hours": 5,
            "include_guide": True,
            "maximum_spaces": 10,
            "difficulty_level": "Medium",
            "language": "Español",
            "available_slots": 10,
            "availabilities": []
        },
        "metadata": {"supplier_id": supplier.id, "unit_price": 100.0, "currency": "USD"}
    }
    response = ninja_client.post("/products/activity-complete/", json=payload)
    assert response.status_code == 422
    assert "date" in response.content.decode() or "past" in response.content.decode()

@pytest.mark.django_db
def test_crear_actividad_completa_valor_negativo(ninja_client, supplier, location):
    today = date.today()
    payload = {
        "data": {
            "name": "Excursión Test",
            "description": "Desc",
            "location_id": location.id,
            "date": str(today + timedelta(days=2)),
            "start_time": "08:00:00",
            "duration_hours": -1,
            "include_guide": True,
            "maximum_spaces": 10,
            "difficulty_level": "Medium",
            "language": "Español",
            "available_slots": 10,
            "availabilities": []
        },
        "metadata": {"supplier_id": supplier.id, "unit_price": 100.0, "currency": "USD"}
    }
    response = ninja_client.post("/products/activity-complete/", json=payload)
    assert response.status_code == 422
    assert "duration_hours" in response.content.decode() or "mayor" in response.content.decode()

@pytest.mark.django_db
def test_crear_transporte_completo_exitoso(ninja_client, supplier, location):
    today = date.today()
    payload = {
        "data": {
            "origin_id": location.id,
            "destination_id": location.id,
            "type": "bus",
            "description": "Servicio Bariloche - El Bolsón, con wifi y aire acondicionado.",
            "notes": "Parada en Lago Puelo.",
            "capacity": 50,
            "availabilities": [
                {
                    "departure_date": str(today + timedelta(days=5)),
                    "departure_time": "09:00:00",
                    "arrival_date": str(today + timedelta(days=5)),
                    "arrival_time": "12:00:00",
                    "total_seats": 50,
                    "reserved_seats": 0,
                    "price": 150.0,
                    "currency": "USD",
                    "state": "active"
                },
                {
                    "departure_date": str(today + timedelta(days=6)),
                    "departure_time": "09:00:00",
                    "arrival_date": str(today + timedelta(days=6)),
                    "arrival_time": "12:00:00",
                    "total_seats": 50,
                    "reserved_seats": 5,
                    "price": 150.0,
                    "currency": "USD",
                    "state": "active"
                }
            ]
        },
        "metadata": {
            "supplier_id": supplier.id,
            "unit_price": 150.0
        }
    }
    response = ninja_client.post("/products/transport-complete/", json=payload)
    if response.status_code != 200:
        print("\nRespuesta de error TRANSPORT COMPLETE:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "transportation"
    assert data["unit_price"] == 150.0
    assert "id" in data
    prod = data["product"]
    assert prod["origin"]["city"] == location.city
    assert prod["destination"]["city"] == location.city
    assert prod["type"] == "bus"
    assert prod["description"] == "Servicio Bariloche - El Bolsón, con wifi y aire acondicionado."
    assert prod["notes"] == "Parada en Lago Puelo."
    assert prod["capacity"] == 50
    from api.products.models import Transportation
    assert Transportation.objects.filter(description__icontains="Bariloche").exists()

@pytest.mark.django_db
@pytest.mark.parametrize("campo", [
    "origin_id", "destination_id", "type", "description", "capacity"
])
def test_crear_transporte_completo_faltante_obligatorio(ninja_client, supplier, location, campo):
    today = date.today()
    base = {
        "origin_id": location.id,
        "destination_id": location.id,
        "type": "bus",
        "description": "Servicio Test",
        "notes": "",
        "capacity": 40,
        "availabilities": []
    }
    base.pop(campo)
    payload = {
        "data": base,
        "metadata": {"supplier_id": supplier.id, "unit_price": 100.0}
    }
    response = ninja_client.post("/products/transport-complete/", json=payload)
    assert response.status_code == 422
    assert campo in response.content.decode()

@pytest.mark.django_db
def test_crear_transporte_completo_fecha_invalida(ninja_client, supplier, location):
    today = date.today()
    payload = {
        "data": {
            "origin_id": location.id,
            "destination_id": location.id,
            "type": "bus",
            "description": "Servicio Test",
            "notes": "",
            "capacity": 40,
            "availabilities": [
                {
                    "departure_date": str(today - timedelta(days=1)),
                    "departure_time": "09:00:00",
                    "arrival_date": str(today + timedelta(days=1)),
                    "arrival_time": "12:00:00",
                    "total_seats": 40,
                    "reserved_seats": 0,
                    "price": 100.0,
                    "currency": "USD",
                    "state": "active"
                }
            ]
        },
        "metadata": {"supplier_id": supplier.id, "unit_price": 100.0}
    }
    response = ninja_client.post("/products/transport-complete/", json=payload)
    assert response.status_code == 422
    assert "departure_date" in response.content.decode() or "past" in response.content.decode()

@pytest.mark.django_db
def test_crear_transporte_completo_valor_negativo(ninja_client, supplier, location):
    today = date.today()
    payload = {
        "data": {
            "origin_id": location.id,
            "destination_id": location.id,
            "type": "bus",
            "description": "Servicio Test",
            "notes": "",
            "capacity": -5,
            "availabilities": []
        },
        "metadata": {"supplier_id": supplier.id, "unit_price": 100.0}
    }
    response = ninja_client.post("/products/transport-complete/", json=payload)
    assert response.status_code == 422
    assert "capacity" in response.content.decode() or "mayor" in response.content.decode() 