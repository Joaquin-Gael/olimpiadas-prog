import logging
from django.db import transaction
from api.products.models import ActivityAvailability, TransportationAvailability, RoomAvailability, Flights

logger = logging.getLogger(__name__)

class InsufficientStockError(ValueError):
    """Excepción para indicar falta de stock suficiente."""
    pass

# ─────────────────────────────────────────────
# Servicios de reserva y liberación de cupos
# ─────────────────────────────────────────────

# ACTIVIDADES
@transaction.atomic
def reserve_activity(avail_id: int, qty: int):
    """Resta `qty` asientos a una disponibilidad de actividad."""
    if qty <= 0:
        logger.warning(f"Intento de reservar qty inválido: {qty} (activity_avail_id={avail_id})")
        raise ValueError("qty debe ser positivo")
    av = ActivityAvailability.objects.select_for_update().get(pk=avail_id)
    remaining = av.total_seats - av.reserved_seats
    if remaining < qty:
        logger.warning(
            "Stock insuficiente (activity %s): solicitados %s, disponibles %s",
            avail_id, qty, remaining
        )
        raise InsufficientStockError("No hay asientos suficientes")
    av.reserved_seats += qty
    av.save(update_fields=["reserved_seats"])
    logger.info(f"Reservados {qty} asientos en actividad {avail_id}. Restantes: {av.total_seats - av.reserved_seats}")
    return {'remaining': av.total_seats - av.reserved_seats}

@transaction.atomic
def release_activity(avail_id: int, qty: int):
    """Devuelve `qty` asientos (por cancelación o expiración)."""
    if qty <= 0:
        logger.warning(f"Intento de liberar qty inválido: {qty} (activity_avail_id={avail_id})")
        raise ValueError("qty debe ser positivo")
    av = ActivityAvailability.objects.select_for_update().get(pk=avail_id)
    av.reserved_seats = max(0, av.reserved_seats - qty)
    av.save(update_fields=["reserved_seats"])
    logger.info(f"Liberados {qty} asientos en actividad {avail_id}. Restantes: {av.total_seats - av.reserved_seats}")
    return {'remaining': av.total_seats - av.reserved_seats}

# TRANSPORTE
@transaction.atomic
def reserve_transportation(avail_id: int, qty: int):
    """Resta `qty` asientos a una disponibilidad de transporte."""
    if qty <= 0:
        logger.warning(f"Intento de reservar qty inválido: {qty} (transport_avail_id={avail_id})")
        raise ValueError("qty debe ser positivo")
    av = TransportationAvailability.objects.select_for_update().get(pk=avail_id)
    remaining = av.total_seats - av.reserved_seats
    if remaining < qty:
        logger.warning(
            "Stock insuficiente (transport %s): solicitados %s, disponibles %s",
            avail_id, qty, remaining
        )
        raise InsufficientStockError("No hay asientos suficientes en transporte")
    av.reserved_seats += qty
    av.save(update_fields=["reserved_seats"])
    logger.info(f"Reservados {qty} asientos en transporte {avail_id}. Restantes: {av.total_seats - av.reserved_seats}")
    return {'remaining': av.total_seats - av.reserved_seats}

@transaction.atomic
def release_transportation(avail_id: int, qty: int):
    """Devuelve `qty` asientos de transporte (por cancelación o expiración)."""
    if qty <= 0:
        logger.warning(f"Intento de liberar qty inválido: {qty} (transport_avail_id={avail_id})")
        raise ValueError("qty debe ser positivo")
    av = TransportationAvailability.objects.select_for_update().get(pk=avail_id)
    av.reserved_seats = max(0, av.reserved_seats - qty)
    av.save(update_fields=["reserved_seats"])
    logger.info(f"Liberados {qty} asientos en transporte {avail_id}. Restantes: {av.total_seats - av.reserved_seats}")
    return {'remaining': av.total_seats - av.reserved_seats}

# HABITACIONES
@transaction.atomic
def reserve_room_availability(avail_id: int, qty: int):
    """Resta `qty` habitaciones disponibles en un rango de fechas."""
    if qty <= 0:
        logger.warning(f"Intento de reservar qty inválido: {qty} (room_avail_id={avail_id})")
        raise ValueError("qty debe ser positivo")
    av = RoomAvailability.objects.select_for_update().get(pk=avail_id)
    if av.available_quantity < qty:
        logger.warning(
            "Stock insuficiente (room_avail %s): solicitados %s, disponibles %s",
            avail_id, qty, av.available_quantity
        )
        raise InsufficientStockError("No hay habitaciones suficientes disponibles")
    av.available_quantity -= qty
    av.save(update_fields=["available_quantity"])
    logger.info(f"Reservadas {qty} habitaciones en disponibilidad {avail_id}. Restantes: {av.available_quantity}")
    return {'remaining': av.available_quantity}

@transaction.atomic
def release_room_availability(avail_id: int, qty: int):
    """Devuelve `qty` habitaciones disponibles (por cancelación o expiración)."""
    if qty <= 0:
        logger.warning(f"Intento de liberar qty inválido: {qty} (room_avail_id={avail_id})")
        raise ValueError("qty debe ser positivo")
    av = RoomAvailability.objects.select_for_update().get(pk=avail_id)
    # Usar max_quantity explícito
    av.available_quantity = min(av.max_quantity, av.available_quantity + qty)
    av.save(update_fields=["available_quantity"])
    logger.info(f"Liberadas {qty} habitaciones en disponibilidad {avail_id}. Restantes: {av.available_quantity}")
    return {'remaining': av.available_quantity}

# VUELOS
@transaction.atomic
def reserve_flight(flight_id: int, qty: int):
    """Resta `qty` asientos disponibles en un vuelo."""
    if qty <= 0:
        logger.warning(f"Intento de reservar qty inválido: {qty} (flight_id={flight_id})")
        raise ValueError("qty debe ser positivo")
    flight = Flights.objects.select_for_update().get(pk=flight_id)
    if flight.available_seats < qty:
        logger.warning(
            "Stock insuficiente (flight %s): solicitados %s, disponibles %s",
            flight_id, qty, flight.available_seats
        )
        raise InsufficientStockError("No hay asientos suficientes en el vuelo")
    flight.available_seats -= qty
    flight.save(update_fields=["available_seats"])
    logger.info(f"Reservados {qty} asientos en vuelo {flight_id}. Restantes: {flight.available_seats}")
    return {'remaining': flight.available_seats}

@transaction.atomic
def release_flight(flight_id: int, qty: int):
    """Devuelve `qty` asientos disponibles en un vuelo (por cancelación o expiración)."""
    if qty <= 0:
        logger.warning(f"Intento de liberar qty inválido: {qty} (flight_id={flight_id})")
        raise ValueError("qty debe ser positivo")
    flight = Flights.objects.select_for_update().get(pk=flight_id)
    # Usar capacity explícito
    flight.available_seats = min(flight.capacity, flight.available_seats + qty)
    flight.save(update_fields=["available_seats"])
    logger.info(f"Liberados {qty} asientos en vuelo {flight_id}. Restantes: {flight.available_seats}")
    return {'remaining': flight.available_seats}

# ─────────────────────────────────────────────
# Estas funciones pueden ser llamadas desde la lógica del carrito, expiración, etc.
# Ejemplo de uso:
# try:
#     reserve_activity(avail_id, cantidad)
# except InsufficientStockError as e:
#     # Responder con error 409 o similar
#
# Para liberar:
# release_activity(avail_id, cantidad)
# ───────────────────────────────────────────── 