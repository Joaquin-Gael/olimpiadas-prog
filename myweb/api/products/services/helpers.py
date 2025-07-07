from ..schemas import (
    ProductsMetadataOut,
    ActivityOut,
    FlightOut,
    LodgmentOut,
    TransportationOut
)
from ..models import ProductsMetadata, RoomAvailability
from typing import Dict, Any
from api.products.models import Activities, Flights, Lodgments, Transportation
from api.products.models import Location

from rich.console import Console
console = Console()

def serialize_product_metadata(metadata: ProductsMetadata) -> Dict[str, Any]:
    """Serializa un objeto ProductsMetadata a un diccionario"""
    base_data = {
        "id": metadata.id,
        "unit_price": float(metadata.unit_price) if metadata.unit_price else 0.0,
        "currency": metadata.currency,
        "product_type": metadata.product_type,
    }
    
    # Verificar que el contenido existe antes de acceder
    if not hasattr(metadata, 'content') or metadata.content is None:
        base_data["product"] = None
        return base_data
    
    # Agregar datos específicos del producto según su tipo
    try:
        if metadata.product_type == "activity":
            activity = metadata.content
            # Obtener las disponibilidades de la actividad
            availabilities = activity.availabilities.all().order_by('event_date', 'start_time')

            base_data["product"] = {
                "id": activity.id,
                "name": activity.name,
                "description": activity.description,
                "location": {
                    "country": activity.location.country if activity.location else "",
                    "state": activity.location.state if activity.location else "",
                    "city": activity.location.city if activity.location else "",
                },
                "date": activity.date,
                "start_time": activity.start_time,
                "duration_hours": activity.duration_hours,
                "include_guide": activity.include_guide,
                "maximum_spaces": activity.maximum_spaces,
                "difficulty_level": activity.difficulty_level,
                "language": activity.language,
                "available_slots": activity.available_slots,
                "availability_id": [
                    {
                        "id": av.id,
                        "event_date": av.event_date,
                        "start_time": av.start_time,
                        "total_seats": av.total_seats,
                        "reserved_seats": av.reserved_seats,
                        "available_seats": av.total_seats - av.reserved_seats,
                        "price": float(av.price),
                        "currency": av.currency,
                        "state": av.state,
                    }
                    for av in availabilities
                ]
            }
        elif metadata.product_type == "flight":
            flight = metadata.content
            base_data["product"] = {
                "id": flight.id,
                "availability_id": flight.id,
                "airline": flight.airline,
                "flight_number": flight.flight_number,
                "origin": {
                    "country": flight.origin.country if flight.origin else "",
                    "state": flight.origin.state if flight.origin else "",
                    "city": flight.origin.city if flight.origin else "",
                },
                "destination": {
                    "country": flight.destination.country if flight.destination else "",
                    "state": flight.destination.state if flight.destination else "",
                    "city": flight.destination.city if flight.destination else "",
                },
                "departure_date": flight.departure_date,
                "departure_time": flight.departure_time,
                "arrival_date": flight.arrival_date,
                "arrival_time": flight.arrival_time,
                "duration_hours": flight.duration_hours,
                "class_flight": flight.class_flight,
                "capacity": flight.capacity,
                "available_seats": flight.available_seats,
                "reserved_seats": flight.capacity - flight.available_seats,
                "luggage_info": flight.luggage_info,
                "aircraft_type": flight.aircraft_type,
                "terminal": flight.terminal,
                "gate": flight.gate,
                "notes": flight.notes,
            }
        elif metadata.product_type == "lodgment":
            lodgment = metadata.content
            # Optimizar: usar prefetch_related si está disponible, sino hacer consulta eficiente
            if hasattr(lodgment, '_prefetched_objects_cache') and 'rooms' in lodgment._prefetched_objects_cache:
                # Si ya está prefetcheado, usar directamente
                rooms = lodgment._prefetched_objects_cache['rooms']
            else:
                # Si no está prefetcheado, hacer una consulta optimizada
                rooms = list(lodgment.rooms.all().values(
                    'id', 'lodgment_id', 'name', 'room_type', 'description', 'capacity',
                    'has_private_bathroom', 'has_balcony', 'has_air_conditioning', 'has_wifi',
                    'base_price_per_night', 'currency', 'is_active', 'created_at', 'updated_at'
                ))
            
            # Obtener disponibilidades de habitaciones
            room_availabilities = {}
            for room in rooms:
                room_id = room.id if hasattr(room, 'id') else room['id']
                # Obtener disponibilidades para esta habitación
                if hasattr(room, 'availabilities'):
                    availabilities = room.availabilities.all().order_by('start_date')
                else:
                    # Si no está prefetcheado, hacer consulta
                    from api.products.models import RoomAvailability
                    availabilities = RoomAvailability.objects.filter(room_id=room_id).order_by('start_date')
                
                room_availabilities[room_id] = [
                    {
                        "id": av.id,
                        "start_date": av.start_date,
                        "end_date": av.end_date,
                        "available_quantity": av.available_quantity,
                        "max_quantity": av.max_quantity,
                        "price_override": float(av.price_override) if av.price_override else None,
                        "currency": av.currency,
                        "is_blocked": av.is_blocked,
                        "minimum_stay": av.minimum_stay,
                        "effective_price": float(av.effective_price),
                        "is_available_for_booking": av.is_available_for_booking,
                    }
                    for av in availabilities
                ]
            
            # Para alojamientos, el available_id es el ID de la primera disponibilidad de habitación disponible
            available_id = None
            for room_id, availabilities in room_availabilities.items():
                if availabilities:
                    available_id = availabilities[0]['id']
                    break
            
            base_data["available_id"] = available_id
            base_data["product"] = {
                "id": lodgment.id,
                "name": lodgment.name,
                "description": lodgment.description,
                "location": {
                    "country": lodgment.location.country if lodgment.location else "",
                    "state": lodgment.location.state if lodgment.location else "",
                    "city": lodgment.location.city if lodgment.location else "",
                },
                "type": lodgment.type,
                "max_guests": lodgment.max_guests,
                "contact_phone": lodgment.contact_phone,
                "contact_email": lodgment.contact_email,
                "amenities": lodgment.amenities or [],
                "date_checkin": lodgment.date_checkin,
                "date_checkout": lodgment.date_checkout,
                "created_at": lodgment.created_at,
                "updated_at": lodgment.updated_at,
                "is_active": lodgment.is_active,
                "rooms": [
                    {
                        "id": room.id if hasattr(room, 'id') else room['id'],
                        "lodgment_id": room.lodgment_id if hasattr(room, 'lodgment_id') else room['lodgment_id'],
                        "name": room.name if hasattr(room, 'name') else room['name'],
                        "room_type": room.room_type if hasattr(room, 'room_type') else room['room_type'],
                        "description": room.description if hasattr(room, 'description') else room['description'],
                        "capacity": room.capacity if hasattr(room, 'capacity') else room['capacity'],
                        "has_private_bathroom": room.has_private_bathroom if hasattr(room, 'has_private_bathroom') else room['has_private_bathroom'],
                        "has_balcony": room.has_balcony if hasattr(room, 'has_balcony') else room['has_balcony'],
                        "has_air_conditioning": room.has_air_conditioning if hasattr(room, 'has_air_conditioning') else room['has_air_conditioning'],
                        "has_wifi": room.has_wifi if hasattr(room, 'has_wifi') else room['has_wifi'],
                        "base_price_per_night": float(room.base_price_per_night) if hasattr(room, 'base_price_per_night') and room.base_price_per_night else float(room['base_price_per_night']) if room['base_price_per_night'] else 0.0,
                        "currency": room.currency if hasattr(room, 'currency') else room['currency'],
                        "is_active": room.is_active if hasattr(room, 'is_active') else room['is_active'],
                        "created_at": room.created_at if hasattr(room, 'created_at') else room['created_at'],
                        "updated_at": room.updated_at if hasattr(room, 'updated_at') else room['updated_at'],
                        "availability_id": room_availabilities.get(room.id if hasattr(room, 'id') else room['id'], [])
                    }
                    for room in rooms
                ]
            }
        elif metadata.product_type == "transportation":
            transportation = metadata.content
            # Obtener las disponibilidades del transporte
            availabilities = transportation.availabilities.all().order_by('departure_date', 'departure_time')

            base_data["product"] = {
                "id": transportation.id,
                "origin": {
                    "country": transportation.origin.country if transportation.origin else "",
                    "state": transportation.origin.state if transportation.origin else "",
                    "city": transportation.origin.city if transportation.origin else "",
                },
                "destination": {
                    "country": transportation.destination.country if transportation.destination else "",
                    "state": transportation.destination.state if transportation.destination else "",
                    "city": transportation.destination.city if transportation.destination else "",
                },
                "type": transportation.type,
                "description": transportation.description,
                "notes": transportation.notes,
                "capacity": transportation.capacity,
                "is_active": transportation.is_active,
                "availability_id": [
                    serialize_transportation_availability(av)
                    for av in availabilities
                ]
            }
        else:
            # Tipo de producto desconocido
            base_data["product"] = None
    except Exception as e:
        console.print_exception(show_locals=True)
        # En caso de error, devolver datos básicos
        base_data["product"] = None
        base_data["error"] = str(e)
    
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

def serialize_lodgment_availability(availability: RoomAvailability) -> Dict[str, Any]:
    """Serializa una disponibilidad de lodgmento"""
    return {
        "id": availability.id,
        "room_id": availability.room.id,
        "available_quantity": availability.available_quantity,
        "start_date": availability.start_date,
        "end_date": availability.end_date,
        "max_quantity": availability.max_quantity,
        "price_override": float(availability.price_override),
        "currency": availability.currency,
        "minimum_stay": availability.minimum_stay,
        "is_blocked": availability.is_blocked,
    }