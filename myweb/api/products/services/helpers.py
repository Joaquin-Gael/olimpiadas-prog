from ..schemas import (
    ProductsMetadataOut,
    ActivityOut,
    FlightOut,
    LodgmentOut,
    TransportationOut
)
from ..models import ProductsMetadata
from typing import Dict, Any
from api.products.models import Activities, Flights, Lodgment, Transportation
from api.products.models import Location

def serialize_product_metadata(metadata: ProductsMetadata) -> Dict[str, Any]:
    """Serializa un objeto ProductsMetadata a un diccionario"""
    base_data = {
        "id": metadata.id,
        "unit_price": metadata.unit_price,
        "currency": metadata.currency,
        "product_type": metadata.product_type,
    }
    
    # Agregar datos específicos del producto según su tipo
    if metadata.product_type == "activity":
        activity = metadata.content
        base_data["product"] = {
            "id": activity.id,
            "name": activity.name,
            "description": activity.description,
            "location": {
                "country": activity.location.country,
                "state": activity.location.state,
                "city": activity.location.city,
            },
            "date": activity.date,
            "start_time": activity.start_time,
            "duration_hours": activity.duration_hours,
            "include_guide": activity.include_guide,
            "maximum_spaces": activity.maximum_spaces,
            "difficulty_level": activity.difficulty_level,
            "language": activity.language,
            "available_slots": activity.available_slots,
        }
    elif metadata.product_type == "flight":
        flight = metadata.content
        base_data["product"] = {
            "id": flight.id,
            "airline": flight.airline,
            "flight_number": flight.flight_number,
            "origin": {
                "country": flight.origin.country,
                "state": flight.origin.state,
                "city": flight.origin.city,
            },
            "destination": {
                "country": flight.destination.country,
                "state": flight.destination.state,
                "city": flight.destination.city,
            },
            "departure_date": flight.departure_date,
            "departure_time": flight.departure_time,
            "arrival_date": flight.arrival_date,
            "arrival_time": flight.arrival_time,
            "duration_hours": flight.duration_hours,
            "class_flight": flight.class_flight,
            "available_seats": flight.available_seats,
            "luggage_info": flight.luggage_info,
            "aircraft_type": flight.aircraft_type,
            "terminal": flight.terminal,
            "gate": flight.gate,
            "notes": flight.notes,
        }
    elif metadata.product_type == "lodgment":
        lodgment = metadata.content
        base_data["product"] = {
            "id": lodgment.id,
            "name": lodgment.name,
            "description": lodgment.description,
            "location": {
                "country": lodgment.location.country,
                "state": lodgment.location.state,
                "city": lodgment.location.city,
            },
            "type": lodgment.type,
            "max_guests": lodgment.max_guests,
            "contact_phone": lodgment.contact_phone,
            "contact_email": lodgment.contact_email,
            "amenities": lodgment.amenities,
            "date_checkin": lodgment.date_checkin,
            "date_checkout": lodgment.date_checkout,
            "created_at": lodgment.created_at,
            "updated_at": lodgment.updated_at,
            "is_active": lodgment.is_active,
            "rooms": [
                {
                    "id": room.id,
                    "lodgment_id": room.lodgment_id,
                    "name": room.name,
                    "room_type": room.room_type,
                    "description": room.description,
                    "capacity": room.capacity,
                    "has_private_bathroom": room.has_private_bathroom,
                    "has_balcony": room.has_balcony,
                    "has_air_conditioning": room.has_air_conditioning,
                    "has_wifi": room.has_wifi,
                    "base_price_per_night": room.base_price_per_night,
                    "currency": room.currency,
                    "is_active": room.is_active,
                    "created_at": room.created_at,
                    "updated_at": room.updated_at,
                }
                for room in lodgment.rooms.all()
            ]
        }
    elif metadata.product_type == "transportation":
        transportation = metadata.content
        base_data["product"] = {
            "id": transportation.id,
            "origin": {
                "country": transportation.origin.country,
                "state": transportation.origin.state,
                "city": transportation.origin.city,
            },
            "destination": {
                "country": transportation.destination.country,
                "state": transportation.destination.state,
                "city": transportation.destination.city,
            },
            "type": transportation.type,
            "description": transportation.description,
            "notes": transportation.notes,
            "capacity": transportation.capacity,
            "is_active": transportation.is_active,
        }
    
    return base_data

def serialize_activity_availability(availability) -> Dict[str, Any]:
    """Serializa una disponibilidad de actividad"""
    return {
        "id": availability.id,
        "activity_id": availability.activity.id,
        "event_date": availability.event_date,
        "start_time": availability.start_time,
        "total_seats": availability.total_seats,
        "reserved_seats": availability.reserved_seats,
        "price": float(availability.price),
        "currency": availability.currency,
        "state": availability.state,
    }

def serialize_transportation_availability(availability) -> Dict[str, Any]:
    """Serializa una disponibilidad de transporte"""
    return {
        "id": availability.id,
        "transportation_id": availability.transportation.id,
        "departure_date": availability.departure_date,
        "departure_time": availability.departure_time,
        "arrival_date": availability.arrival_date,
        "arrival_time": availability.arrival_time,
        "total_seats": availability.total_seats,
        "reserved_seats": availability.reserved_seats,
        "price": float(availability.price),
        "currency": availability.currency,
        "state": availability.state,
    }