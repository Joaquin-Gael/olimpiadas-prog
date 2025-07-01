import pytest
from datetime import date, timedelta, time
from api.products.models import Activities, Flights, Lodgment, Room
import random

@pytest.mark.django_db
def test_create_valid_complete_activity(ninja_client, supplier, location):
    """Complete test for creating an activity with all fields"""
    payload = {
        "product_type": "activity",
        "unit_price": 150.0,
        "supplier_id": supplier.id,
        "product": {
            "name": "Rafting on the Manso River",
            "description": "Intermediate level rafting adventure on the Manso River, includes equipment and professional guide.",
            "location_id": location.id,
            "date": str(date.today() + timedelta(days=10)),
            "start_time": "08:30:00",
            "duration_hours": 6,
            "include_guide": True,
            "maximum_spaces": 20,
            "difficulty_level": "Medium",
            "language": "English",
            "available_slots": 20
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 200:
        print("\nError response COMPLETE ACTIVITY:", response.status_code, response.content)
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
    assert prod["language"] == "English"
    assert prod["available_slots"] == 20
    assert "location" in prod
    assert prod["location"]["city"] == location.city
    # Validate existence in database
    assert Activities.objects.filter(name="Rafting on the Manso River").exists()

@pytest.mark.django_db
def test_create_valid_activity_required_fields(ninja_client, supplier, location):
    """Test for creating an activity with only required fields"""
    payload = {
        "product_type": "activity",
        "unit_price": 100.0,
        "supplier_id": supplier.id,
        "product": {
            "name": "Otto Hill Trekking",
            "description": "Guided walk to Otto Hill",
            "location_id": location.id,
            "date": str(date.today() + timedelta(days=5)),
            "start_time": "10:00:00",
            "duration_hours": 3,
            "include_guide": False,
            "maximum_spaces": 10,
            "difficulty_level": "Easy",
            "language": "English",
            "available_slots": 10
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 200:
        print("\nError response REQUIRED FIELDS ACTIVITY:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "activity"
    assert data["unit_price"] == 100.0
    assert data["product"]["name"] == "Otto Hill Trekking"
    assert Activities.objects.filter(name="Otto Hill Trekking").exists()

@pytest.mark.django_db
@pytest.mark.parametrize("field", [
    "name", "description", "location_id", "date", "start_time", "duration_hours", "include_guide", "maximum_spaces", "difficulty_level", "language", "available_slots"
])
def test_create_activity_missing_required_field(ninja_client, supplier, location, field):
    """Error test: missing required field"""
    base = {
        "name": "Lake Kayaking",
        "description": "Guided lake paddling",
        "location_id": location.id,
        "date": str(date.today() + timedelta(days=7)),
        "start_time": "11:00:00",
        "duration_hours": 2,
        "include_guide": True,
        "maximum_spaces": 8,
        "difficulty_level": "Easy",
        "language": "English",
        "available_slots": 8
    }
    base.pop(field)
    payload = {
        "product_type": "activity",
        "unit_price": 90.0,
        "supplier_id": supplier.id,
        "product": base
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 422:
        print(f"\nError response MISSING FIELD {field}:", response.status_code, response.content)
    assert response.status_code == 422
    assert field in response.content.decode()

@pytest.mark.django_db
@pytest.mark.parametrize("field,value", [
    ("duration_hours", -1),
    ("maximum_spaces", -5),
    ("available_slots", -2),
    ("date", str(date.today() - timedelta(days=1))),
    ("difficulty_level", "SuperHard"),
])
def test_create_activity_invalid_value(ninja_client, supplier, location, field, value):
    """Error test: invalid value in field"""
    base = {
        "name": "Canopy",
        "description": "Forest zipline",
        "location_id": location.id,
        "date": str(date.today() + timedelta(days=3)),
        "start_time": "12:00:00",
        "duration_hours": 2,
        "include_guide": True,
        "maximum_spaces": 10,
        "difficulty_level": "Medium",
        "language": "English",
        "available_slots": 10
    }
    base[field] = value
    payload = {
        "product_type": "activity",
        "unit_price": 120.0,
        "supplier_id": supplier.id,
        "product": base
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 422:
        print(f"\nError response INVALID VALUE {field}:", response.status_code, response.content)
    assert response.status_code == 422
    assert field in response.content.decode()

@pytest.mark.django_db
def test_create_activity_invalid_logic(ninja_client, supplier, location):
    """Error test: date in the past and negative seats"""
    payload = {
        "product_type": "activity",
        "unit_price": 120.0,
        "supplier_id": supplier.id,
        "product": {
            "name": "Lake Walk",
            "description": "Guided walk to hidden lake",
            "location_id": location.id,
            "date": str(date.today() - timedelta(days=1)),
            "start_time": "09:00:00",
            "duration_hours": 4,
            "include_guide": True,
            "maximum_spaces": -5,
            "difficulty_level": "Easy",
            "language": "English",
            "available_slots": 15
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 422:
        print("\nError response LOGIC:", response.status_code, response.content)
    assert response.status_code == 422
    assert "date" in response.content.decode() or "maximum_spaces" in response.content.decode()

@pytest.mark.django_db
def test_create_activity_nonexistent_supplier(ninja_client, location):
    """Test for creating an activity with nonexistent supplier"""
    payload = {
        "product_type": "activity",
        "unit_price": 120.0,
        "supplier_id": 99999,  # ID that doesn't exist
        "product": {
            "name": "Lake Walk",
            "description": "Guided walk to hidden lake",
            "location_id": location.id,
            "date": str(date.today() + timedelta(days=5)),
            "start_time": "09:00:00",
            "duration_hours": 4,
            "include_guide": True,
            "maximum_spaces": 15,
            "difficulty_level": "Easy",
            "language": "English",
            "available_slots": 15
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    assert response.status_code == 404

@pytest.mark.django_db
def test_create_valid_complete_flight(ninja_client, supplier, location):
    """Complete test for creating a flight with all fields"""
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
            "luggage_info": "1 suitcase 23kg + 1 carry-on bag",
            "aircraft_type": "Boeing 737",
            "terminal": "A",
            "gate": "12",
            "notes": "Priority boarding"
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 200:
        print("\nError response COMPLETE FLIGHT:", response.status_code, response.content)
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
    assert prod["luggage_info"] == "1 suitcase 23kg + 1 carry-on bag"
    assert prod["aircraft_type"] == "Boeing 737"
    assert prod["terminal"] == "A"
    assert prod["gate"] == "12"
    assert prod["notes"] == "Priority boarding"
    # Validate existence in database
    assert Flights.objects.filter(flight_number="AR1234").exists()

@pytest.mark.django_db
def test_create_valid_flight_required_fields(ninja_client, supplier, location):
    """Test for creating a flight with only required fields"""
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
            "luggage_info": "Carry-on bag only",
            "aircraft_type": "Airbus A320"
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 200:
        print("\nError response REQUIRED FIELDS FLIGHT:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "flight"
    assert data["unit_price"] == 200.0
    assert data["product"]["flight_number"] == "JS5678"
    assert Flights.objects.filter(flight_number="JS5678").exists()

@pytest.mark.django_db
@pytest.mark.parametrize("field", [
    "airline", "flight_number", "origin_id", "destination_id", "departure_date", "departure_time", "arrival_date", "arrival_time", "duration_hours", "class_flight", "available_seats", "luggage_info", "aircraft_type"
])
def test_create_flight_missing_required_field(ninja_client, supplier, location, field):
    """Error test: missing required field in flight"""
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
        "luggage_info": "1 suitcase",
        "aircraft_type": "Boeing 777"
    }
    base.pop(field)
    payload = {
        "product_type": "flight",
        "unit_price": 180.0,
        "supplier_id": supplier.id,
        "product": base
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 422:
        print(f"\nError response MISSING FIELD {field}:", response.status_code, response.content)
    assert response.status_code == 422
    assert field in response.content.decode()

@pytest.mark.django_db
@pytest.mark.parametrize("field,value", [
    ("duration_hours", -1),
    ("available_seats", -5),
    ("departure_date", str(date.today() - timedelta(days=1))),
    ("arrival_date", str(date.today() - timedelta(days=2))),
    ("class_flight", "SuperLuxury"),
])
def test_create_flight_invalid_value(ninja_client, supplier, location, field, value):
    """Error test: invalid value in flight field"""
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
        "luggage_info": "1 bag",
        "aircraft_type": "Embraer 190"
    }
    base[field] = value
    payload = {
        "product_type": "flight",
        "unit_price": 120.0,
        "supplier_id": supplier.id,
        "product": base
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 422:
        print(f"\nError response INVALID VALUE {field}:", response.status_code, response.content)
    assert response.status_code == 422
    content = response.content.decode()
    if field == "departure_date":
        assert "Departure date cannot be in the past." in content
    elif field == "arrival_date":
        assert "Arrival date must be after departure date." in content
    else:
        assert field in content

@pytest.mark.django_db
def test_create_flight_invalid_logic(ninja_client, supplier, location):
    """Error test: arrival before departure and negative seats"""
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
            "arrival_date": str(date.today() + timedelta(days=4)),  # arrival before
            "arrival_time": "09:00:00",
            "duration_hours": 2,
            "class_flight": "Economy",
            "available_seats": -10,
            "luggage_info": "1 bag",
            "aircraft_type": "Boeing 737"
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 422:
        print("\nError response LOGIC:", response.status_code, response.content)
    assert response.status_code == 422
    assert "arrival_date" in response.content.decode() or "available_seats" in response.content.decode()

@pytest.mark.django_db
def test_create_valid_complete_lodgment(ninja_client, supplier, location):
    """Complete test for creating a lodgment with realistic production data"""
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
            "amenities": ["wifi", "spa", "pool", "breakfast"],
            "date_checkin": str(date.today() + timedelta(days=30)),
            "date_checkout": str(date.today() + timedelta(days=35))
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 200:
        print("\nError response LODGMENT COMPLETE:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "lodgment"
    assert data["unit_price"] == 800.0
    assert "id" in data
    prod = data["product"]
    assert prod["name"] == payload["product"]["name"]
    assert prod["description"] == payload["product"]["description"]
    assert prod["location"]["city"] == location.city
    assert prod["type"] == "hotel"
    assert prod["max_guests"] == 4
    assert prod["contact_phone"] == "+54 294 5555555"
    assert prod["contact_email"] == "info@patagoniasur.com"
    assert set(prod["amenities"]) == set(["wifi", "spa", "pool", "breakfast"])
    assert prod["date_checkin"] == payload["product"]["date_checkin"]
    assert prod["date_checkout"] == payload["product"]["date_checkout"]
    # Validate existence in database
    assert Lodgment.objects.filter(name="Hotel Patagonia Sur").exists()

@pytest.mark.django_db
def test_create_valid_complete_transportation(ninja_client, supplier, location):
    """Complete test for creating transportation with realistic production data"""
    payload = {
        "product_type": "transportation",
        "unit_price": 250.0,
        "supplier_id": supplier.id,
        "product": {
            "origin_id": location.id,
            "destination_id": location.id,
            "type": "bus",
            "description": "Bus service Bariloche - Villa La Angostura, with air conditioning and wifi.",
            "notes": "Intermediate stop in Dina Huapi.",
            "capacity": 45
        }
    }
    response = ninja_client.post("/products/create/", json=payload)
    if response.status_code != 200:
        print("\nError response TRANSPORTATION:", response.status_code, response.content)
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
    assert prod["description"] == "Bus service Bariloche - Villa La Angostura, with air conditioning and wifi."
    assert prod["notes"] == "Intermediate stop in Dina Huapi."
    assert prod["capacity"] == 45

@pytest.mark.django_db
def test_create_complete_lodgment_successful(ninja_client, supplier, location):
    """Successful test for complete lodgment creation with rooms and availabilities"""
    today = date.today()
    payload = {
        "data": {
            "name": "Hotel Patagonia Sur",
            "description": "4-star hotel with lake view and spa.",
            "location_id": location.id,
            "type": "hotel",
            "max_guests": 10,
            "contact_phone": "+54 294 5555555",
            "contact_email": "info@patagoniasur.com",
            "amenities": ["wifi", "spa", "pool", "breakfast"],
            "date_checkin": str(today + timedelta(days=10)),
            "date_checkout": str(today + timedelta(days=15)),
            "rooms": [
                {
                    "room_type": "double",
                    "name": "Superior Double",
                    "description": "Double room with lake view",
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
                    "name": "Family Suite",
                    "description": "Suite for 4 people, ideal for families",
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
        print("\nError response COMPLETE LODGMENT:", response.status_code, response.content)
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
    # Validate rooms
    assert len(prod["rooms"]) == 2
    names = [r["name"] for r in prod["rooms"]]
    assert "Superior Double" in names and "Family Suite" in names
    # Validate existence in database
    assert Lodgment.objects.filter(name="Hotel Patagonia Sur").exists()
    assert Room.objects.filter(name="Superior Double").exists()
    assert Room.objects.filter(name="Family Suite").exists()

@pytest.mark.django_db
@pytest.mark.parametrize("field", [
    "name", "location_id", "type", "max_guests", "date_checkin", "date_checkout", "rooms"
])
def test_complete_lodgment_missing_required_field(ninja_client, supplier, location, field):
    """Error test: missing required field in data"""
    today = date.today()
    base = {
        "name": "Test Hotel",
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
    base.pop(field)
    payload = {
        "data": base,
        "metadata": {"supplier_id": supplier.id, "unit_price": 500.0}
    }
    response = ninja_client.post("/products/lodgment-complete/", json=payload)
    assert response.status_code == 422
    assert field in response.content.decode()

@pytest.mark.django_db
def test_complete_lodgment_invalid_date(ninja_client, supplier, location):
    """Error test: checkin date in the past"""
    today = date.today()
    payload = {
        "data": {
            "name": "Test Hotel",
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
def test_complete_lodgment_negative_quantity(ninja_client, supplier, location):
    """Error test: negative quantity in room availability"""
    today = date.today()
    payload = {
        "data": {
            "name": "Test Hotel",
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
    assert "available_quantity" in response.content.decode() or "greater than or equal to 0" in response.content.decode()

@pytest.mark.django_db
def test_create_complete_activity_successful(ninja_client, supplier, location):
    """Successful test for complete activity creation with availabilities"""
    today = date.today()
    payload = {
        "data": {
            "name": "Tronador Hill Excursion",
            "description": "Full-day trekking with guide and refreshments.",
            "location_id": location.id,
            "date": str(today + timedelta(days=7)),
            "start_time": "07:00:00",
            "duration_hours": 10,
            "include_guide": True,
            "maximum_spaces": 20,
            "difficulty_level": "Hard",
            "language": "English",
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
        print("\nError response COMPLETE ACTIVITY:", response.status_code, response.content)
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
    assert prod["language"] == "English"
    assert prod["available_slots"] == 20
    assert prod["location"]["city"] == location.city
    # Validate existence in database
    assert Activities.objects.filter(name="Tronador Hill Excursion").exists()

@pytest.mark.django_db
@pytest.mark.parametrize("field", [
    "name", "description", "location_id", "date", "start_time", "duration_hours", "include_guide", "maximum_spaces", "difficulty_level", "language", "available_slots"
])
def test_create_complete_activity_missing_required_field(ninja_client, supplier, location, field):
    """Error test: missing required field in complete activity"""
    today = date.today()
    base = {
        "name": "Test Excursion",
        "description": "Desc",
        "location_id": location.id,
        "date": str(today + timedelta(days=5)),
        "start_time": "08:00:00",
        "duration_hours": 5,
        "include_guide": True,
        "maximum_spaces": 10,
        "difficulty_level": "Medium",
        "language": "English",
        "available_slots": 10,
        "availabilities": []
    }
    base.pop(field)
    payload = {
        "data": base,
        "metadata": {"supplier_id": supplier.id, "unit_price": 100.0, "currency": "USD"}
    }
    response = ninja_client.post("/products/activity-complete/", json=payload)
    assert response.status_code == 422
    assert field in response.content.decode()

@pytest.mark.django_db
def test_create_complete_activity_invalid_date(ninja_client, supplier, location):
    """Error test: invalid date in complete activity"""
    today = date.today()
    payload = {
        "data": {
            "name": "Test Excursion",
            "description": "Desc",
            "location_id": location.id,
            "date": str(today - timedelta(days=1)),
            "start_time": "08:00:00",
            "duration_hours": 5,
            "include_guide": True,
            "maximum_spaces": 10,
            "difficulty_level": "Medium",
            "language": "English",
            "available_slots": 10,
            "availabilities": []
        },
        "metadata": {"supplier_id": supplier.id, "unit_price": 100.0, "currency": "USD"}
    }
    response = ninja_client.post("/products/activity-complete/", json=payload)
    assert response.status_code == 422
    assert "date" in response.content.decode() or "past" in response.content.decode()

@pytest.mark.django_db
def test_create_complete_activity_negative_value(ninja_client, supplier, location):
    """Error test: negative value in complete activity"""
    today = date.today()
    payload = {
        "data": {
            "name": "Test Excursion",
            "description": "Desc",
            "location_id": location.id,
            "date": str(today + timedelta(days=2)),
            "start_time": "08:00:00",
            "duration_hours": -1,
            "include_guide": True,
            "maximum_spaces": 10,
            "difficulty_level": "Medium",
            "language": "English",
            "available_slots": 10,
            "availabilities": []
        },
        "metadata": {"supplier_id": supplier.id, "unit_price": 100.0, "currency": "USD"}
    }
    response = ninja_client.post("/products/activity-complete/", json=payload)
    assert response.status_code == 422
    assert "duration_hours" in response.content.decode() or "greater" in response.content.decode()

@pytest.mark.django_db
def test_create_complete_transportation_successful(ninja_client, supplier, location):
    """Successful test for complete transportation creation with availabilities"""
    today = date.today()
    payload = {
        "data": {
            "origin_id": location.id,
            "destination_id": location.id,
            "type": "bus",
            "description": "Bariloche - El Bolsón service, with wifi and air conditioning.",
            "notes": "Stop in Lago Puelo.",
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
        print("\nError response COMPLETE TRANSPORT:", response.status_code, response.content)
    assert response.status_code == 200
    data = response.json()
    assert data["product_type"] == "transportation"
    assert data["unit_price"] == 150.0
    assert "id" in data
    prod = data["product"]
    assert prod["origin"]["city"] == location.city
    assert prod["destination"]["city"] == location.city
    assert prod["type"] == "bus"
    assert prod["description"] == "Bariloche - El Bolsón service, with wifi and air conditioning."
    assert prod["notes"] == "Stop in Lago Puelo."
    assert prod["capacity"] == 50
    from api.products.models import Transportation
    assert Transportation.objects.filter(description__icontains="Bariloche").exists()

@pytest.mark.django_db
@pytest.mark.parametrize("field", [
    "origin_id", "destination_id", "type", "description", "capacity"
])
def test_create_complete_transportation_missing_required_field(ninja_client, supplier, location, field):
    """Error test: missing required field in complete transportation"""
    today = date.today()
    base = {
        "origin_id": location.id,
        "destination_id": location.id,
        "type": "bus",
        "description": "Test Service",
        "notes": "",
        "capacity": 40,
        "availabilities": []
    }
    base.pop(field)
    payload = {
        "data": base,
        "metadata": {"supplier_id": supplier.id, "unit_price": 100.0}
    }
    response = ninja_client.post("/products/transport-complete/", json=payload)
    assert response.status_code == 422
    assert field in response.content.decode()

@pytest.mark.django_db
def test_create_complete_transportation_invalid_date(ninja_client, supplier, location):
    """Error test: invalid date in complete transportation"""
    today = date.today()
    payload = {
        "data": {
            "origin_id": location.id,
            "destination_id": location.id,
            "type": "bus",
            "description": "Test Service",
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
def test_create_complete_transportation_negative_value(ninja_client, supplier, location):
    """Error test: negative value in complete transportation"""
    today = date.today()
    payload = {
        "data": {
            "origin_id": location.id,
            "destination_id": location.id,
            "type": "bus",
            "description": "Test Service",
            "notes": "",
            "capacity": -5,
            "availabilities": []
        },
        "metadata": {"supplier_id": supplier.id, "unit_price": 100.0}
    }
    response = ninja_client.post("/products/transport-complete/", json=payload)
    assert response.status_code == 422
    assert "capacity" in response.content.decode() or "greater" in response.content.decode() 