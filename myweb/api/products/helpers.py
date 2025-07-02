from .schemas import (
    ProductsMetadataOut,
    ActivityOut,
    FlightOut,
    LodgmentOut,
    TransportationOut
)
from .models import ProductsMetadata
from typing import Dict, Any
from api.products.models import Activities, Flights, Lodgments, Transportation
from api.products.models import Location

def serialize_product_metadata(metadata: ProductsMetadata) -> Dict[str, Any]:
    """Serializa la metadata de un producto con su contenido específico"""
    base_data = {
        "id": metadata.id,
        "precio_unitario": metadata.precio_unitario,
        "tipo_producto": metadata.tipo_producto,
    }
    
    # Serializar el producto específico según su tipo
    if metadata.tipo_producto == "activity":
        activity = metadata.content
        location_data = {
            "country": activity.location.country,
            "state": activity.location.state,
            "city": activity.location.city,
        }
        base_data["producto"] = ActivityOut(
            id=activity.id,
            name=activity.name,
            description=activity.description,
            location=location_data,
            date=activity.date,
            start_time=activity.start_time,
            duration_hours=activity.duration_hours,
            include_guide=activity.include_guide,
            maximum_spaces=activity.maximum_spaces,
            difficulty_level=activity.difficulty_level,
            language=activity.language,
            available_slots=activity.available_slots,
        ).dict()
    
    elif metadata.tipo_producto == "flight":
        flight = metadata.content
        origin_data = {
            "country": flight.origin.country,
            "state": flight.origin.state,
            "city": flight.origin.city,
        }
        destination_data = {
            "country": flight.destination.country,
            "state": flight.destination.state,
            "city": flight.destination.city,
        }
        base_data["producto"] = FlightOut(
            id=flight.id,
            airline=flight.airline,
            flight_number=flight.flight_number,
            origin=origin_data,
            destination=destination_data,
            departure_date=flight.departure_date,
            departure_time=flight.departure_time,
            arrival_date=flight.arrival_date,
            arrival_time=flight.arrival_time,
            duration_hours=flight.duration_hours,
            class_flight=flight.class_flight,
            available_seats=flight.available_seats,
            luggage_info=flight.luggage_info,
            aircraft_type=flight.aircraft_type,
            terminal=flight.terminal,
            gate=flight.gate,
            notes=flight.notes,
        ).dict()
    
    elif metadata.tipo_producto == "lodgment":
        lodgment = metadata.content
        location_data = {
            "country": lodgment.location.country,
            "state": lodgment.location.state,
            "city": lodgment.location.city,
        }
        base_data["producto"] = LodgmentOut(
            id=lodgment.id,
            name=lodgment.name,
            description=lodgment.description,
            location=location_data,
            type=lodgment.type,
            max_guests=lodgment.max_guests,
            contact_phone=lodgment.contact_phone,
            contact_email=lodgment.contact_email,
            amenities=lodgment.amenities,
            date_checkin=lodgment.date_checkin,
            date_checkout=lodgment.date_checkout,
            created_at=lodgment.created_at,
            updated_at=lodgment.updated_at,
            is_active=lodgment.is_active,
        ).dict()
    
    elif metadata.tipo_producto == "transportation":
        transportation = metadata.content
        origin_data = {
            "country": transportation.origin.country,
            "state": transportation.origin.state,
            "city": transportation.origin.city,
        }
        destination_data = {
            "country": transportation.destination.country,
            "state": transportation.destination.state,
            "city": transportation.destination.city,
        }
        base_data["producto"] = TransportationOut(
            id=transportation.id,
            origin=origin_data,
            destination=destination_data,
            type=transportation.type,
            description=transportation.description,
            notes=transportation.notes,
            capacity=transportation.capacity,
            is_active=transportation.is_active,
        ).dict()
    
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