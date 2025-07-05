import logging
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils import timezone
from api.products.models import ActivityAvailability, TransportationAvailability, RoomAvailability, Flights
from .audit_services import StockAuditService

logger = logging.getLogger(__name__)

class InsufficientStockError(ValueError):
    """Excepción para indicar falta de stock suficiente."""
    pass

class InvalidQuantityError(ValueError):
    """Excepción para indicar cantidad inválida."""
    pass

class ProductNotFoundError(ValueError):
    """Excepción para indicar que el producto no existe."""
    pass

class StockValidationError(ValueError):
    """Excepción para errores de validación de stock."""
    pass

# ─────────────────────────────────────────────
# FUNCIONES DE VERIFICACIÓN DE STOCK
# ─────────────────────────────────────────────

def check_activity_stock(avail_id: int, qty: int) -> dict:
    """
    Verifica si hay stock suficiente para una actividad sin reservarlo.
    Retorna información del stock disponible.
    """
    if qty <= 0:
        raise InvalidQuantityError("La cantidad debe ser mayor a 0")
    
    try:
        av = ActivityAvailability.objects.get(pk=avail_id)
        remaining = av.total_seats - av.reserved_seats
        
        return {
            'available': remaining,
            'requested': qty,
            'sufficient': remaining >= qty,
            'total_seats': av.total_seats,
            'reserved_seats': av.reserved_seats,
            'availability_id': avail_id
        }
    except ObjectDoesNotExist:
        raise ProductNotFoundError(f"Disponibilidad de actividad {avail_id} no encontrada")

def check_transportation_stock(avail_id: int, qty: int) -> dict:
    """
    Verifica si hay stock suficiente para transporte sin reservarlo.
    Retorna información del stock disponible.
    """
    if qty <= 0:
        raise InvalidQuantityError("La cantidad debe ser mayor a 0")
    
    try:
        av = TransportationAvailability.objects.get(pk=avail_id)
        remaining = av.total_seats - av.reserved_seats
        
        return {
            'available': remaining,
            'requested': qty,
            'sufficient': remaining >= qty,
            'total_seats': av.total_seats,
            'reserved_seats': av.reserved_seats,
            'availability_id': avail_id
        }
    except ObjectDoesNotExist:
        raise ProductNotFoundError(f"Disponibilidad de transporte {avail_id} no encontrada")

def check_room_stock(avail_id: int, qty: int) -> dict:
    """
    Verifica si hay stock suficiente para habitaciones sin reservarlo.
    Retorna información del stock disponible.
    """
    if qty <= 0:
        raise InvalidQuantityError("La cantidad debe ser mayor a 0")
    
    try:
        av = RoomAvailability.objects.get(pk=avail_id)
        
        return {
            'available': av.available_quantity,
            'requested': qty,
            'sufficient': av.available_quantity >= qty,
            'max_quantity': getattr(av, 'max_quantity', None),
            'availability_id': avail_id
        }
    except ObjectDoesNotExist:
        raise ProductNotFoundError(f"Disponibilidad de habitación {avail_id} no encontrada")

def check_flight_stock(flight_id: int, qty: int) -> dict:
    """
    Verifica si hay stock suficiente para un vuelo sin reservarlo.
    Retorna información del stock disponible.
    """
    if qty <= 0:
        raise InvalidQuantityError("La cantidad debe ser mayor a 0")
    
    try:
        flight = Flights.objects.get(pk=flight_id)
        
        return {
            'available': flight.available_seats,
            'requested': qty,
            'sufficient': flight.available_seats >= qty,
            'capacity': getattr(flight, 'capacity', None),
            'flight_id': flight_id
        }
    except ObjectDoesNotExist:
        raise ProductNotFoundError(f"Vuelo {flight_id} no encontrado")

# ─────────────────────────────────────────────
# SERVICIOS DE RESERVA Y LIBERACIÓN MEJORADOS
# ─────────────────────────────────────────────

def reserve_activity(avail_id: int, qty: int, request=None):
    """
    Reserva `qty` asientos de una actividad con validaciones mejoradas y auditoría.
    """
    if qty <= 0:
        error_msg = f"Intento de reservar cantidad inválida: {qty} (activity_avail_id={avail_id})"
        logger.warning(error_msg)
        # Registrar auditoría de error fuera de la transacción
        StockAuditService.log_activity_stock_operation(
            operation_type="reserve",
            availability_id=avail_id,
            quantity=qty,
            request=request,
            success=False,
            error_message=error_msg
        )
        raise InvalidQuantityError("La cantidad debe ser mayor a 0")
    
    try:
        # Usar transacción atómica solo para la operación de stock
        with transaction.atomic():
            try:
                av = ActivityAvailability.objects.select_for_update().get(pk=avail_id)
            except ObjectDoesNotExist:
                error_msg = f"Disponibilidad de actividad {avail_id} no encontrada"
                raise ProductNotFoundError(error_msg)
            
            remaining = av.total_seats - av.reserved_seats
            previous_reserved = av.reserved_seats
            
            if remaining < qty:
                error_msg = f"No hay asientos suficientes. Disponibles: {remaining}, Solicitados: {qty}"
                logger.warning(
                    "Stock insuficiente (activity %s): solicitados %s, disponibles %s",
                    avail_id, qty, remaining
                )
                raise InsufficientStockError(error_msg)
            
            # Validación adicional para evitar stock negativo
            if av.reserved_seats + qty > av.total_seats:
                error_msg = "La reserva excedería la capacidad total"
                raise StockValidationError(error_msg)
            
            av.reserved_seats += qty
            av.save(update_fields=["reserved_seats"])
            
            # Registrar auditoría exitosa
            StockAuditService.log_activity_stock_operation(
                operation_type="reserve",
                availability_id=avail_id,
                quantity=qty,
                previous_reserved=previous_reserved,
                new_reserved=av.reserved_seats,
                request=request,
                success=True
            )
            
            # Actualizar métricas
            StockAuditService.update_stock_metrics(
                product_type="activity",
                product_id=avail_id,
                total_capacity=av.total_seats,
                current_reserved=av.reserved_seats,
                current_available=av.total_seats - av.reserved_seats,
                as_of_date=timezone.now().date()
            )
            
            logger.info(f"Reservados {qty} asientos en actividad {avail_id}. Restantes: {av.total_seats - av.reserved_seats}")
            return {
                'remaining': av.total_seats - av.reserved_seats,
                'reserved': av.reserved_seats,
                'total': av.total_seats
            }
    
    except (ProductNotFoundError, InsufficientStockError, StockValidationError) as e:
        # Registrar auditoría de error fuera de la transacción
        StockAuditService.log_activity_stock_operation(
            operation_type="reserve",
            availability_id=avail_id,
            quantity=qty,
            request=request,
            success=False,
            error_message=str(e)
        )
        raise

@transaction.atomic
def release_activity(avail_id: int, qty: int, request=None):
    """
    Libera `qty` asientos de una actividad con validaciones mejoradas y auditoría.
    """
    if qty <= 0:
        error_msg = f"Intento de liberar cantidad inválida: {qty} (activity_avail_id={avail_id})"
        logger.warning(error_msg)
        # Registrar auditoría de error
        StockAuditService.log_activity_stock_operation(
            operation_type="release",
            availability_id=avail_id,
            quantity=qty,
            request=request,
            success=False,
            error_message=error_msg
        )
        raise InvalidQuantityError("La cantidad debe ser mayor a 0")
    
    try:
        av = ActivityAvailability.objects.select_for_update().get(pk=avail_id)
    except ObjectDoesNotExist:
        error_msg = f"Disponibilidad de actividad {avail_id} no encontrada"
        # Registrar auditoría de error
        StockAuditService.log_activity_stock_operation(
            operation_type="release",
            availability_id=avail_id,
            quantity=qty,
            request=request,
            success=False,
            error_message=error_msg
        )
        raise ProductNotFoundError(error_msg)
    
    previous_reserved = av.reserved_seats
    
    # Validación para evitar asientos reservados negativos
    if av.reserved_seats < qty:
        logger.warning(f"Intento de liberar más asientos de los reservados: reservados={av.reserved_seats}, liberar={qty}")
        qty = av.reserved_seats  # Liberar solo los que están reservados
    
    av.reserved_seats = max(0, av.reserved_seats - qty)
    av.save(update_fields=["reserved_seats"])
    
    # Registrar auditoría exitosa
    StockAuditService.log_activity_stock_operation(
        operation_type="release",
        availability_id=avail_id,
        quantity=qty,
        previous_reserved=previous_reserved,
        new_reserved=av.reserved_seats,
        request=request,
        success=True
    )
    
    # Actualizar métricas
    StockAuditService.update_stock_metrics(
        product_type="activity",
        product_id=avail_id,
        total_capacity=av.total_seats,
        current_reserved=av.reserved_seats,
        current_available=av.total_seats - av.reserved_seats,
        as_of_date=timezone.now().date()
    )
    
    logger.info(f"Liberados {qty} asientos en actividad {avail_id}. Restantes: {av.total_seats - av.reserved_seats}")
    return {
        'remaining': av.total_seats - av.reserved_seats,
        'reserved': av.reserved_seats,
        'total': av.total_seats
    }

@transaction.atomic
def reserve_transportation(avail_id: int, qty: int):
    """
    Reserva `qty` asientos de transporte con validaciones mejoradas.
    """
    if qty <= 0:
        logger.warning(f"Intento de reservar cantidad inválida: {qty} (transport_avail_id={avail_id})")
        raise InvalidQuantityError("La cantidad debe ser mayor a 0")
    
    try:
        av = TransportationAvailability.objects.select_for_update().get(pk=avail_id)
    except ObjectDoesNotExist:
        raise ProductNotFoundError(f"Disponibilidad de transporte {avail_id} no encontrada")
    
    remaining = av.total_seats - av.reserved_seats
    
    if remaining < qty:
        logger.warning(
            "Stock insuficiente (transport %s): solicitados %s, disponibles %s",
            avail_id, qty, remaining
        )
        raise InsufficientStockError(f"No hay asientos suficientes en transporte. Disponibles: {remaining}, Solicitados: {qty}")
    
    # Validación adicional para evitar stock negativo
    if av.reserved_seats + qty > av.total_seats:
        raise StockValidationError("La reserva excedería la capacidad total")
    
    av.reserved_seats += qty
    av.save(update_fields=["reserved_seats"])
    
    logger.info(f"Reservados {qty} asientos en transporte {avail_id}. Restantes: {av.total_seats - av.reserved_seats}")
    return {
        'remaining': av.total_seats - av.reserved_seats,
        'reserved': av.reserved_seats,
        'total': av.total_seats
    }

@transaction.atomic
def release_transportation(avail_id: int, qty: int):
    """
    Libera `qty` asientos de transporte con validaciones mejoradas.
    """
    if qty <= 0:
        logger.warning(f"Intento de liberar cantidad inválida: {qty} (transport_avail_id={avail_id})")
        raise InvalidQuantityError("La cantidad debe ser mayor a 0")
    
    try:
        av = TransportationAvailability.objects.select_for_update().get(pk=avail_id)
    except ObjectDoesNotExist:
        raise ProductNotFoundError(f"Disponibilidad de transporte {avail_id} no encontrada")
    
    # Validación para evitar asientos reservados negativos
    if av.reserved_seats < qty:
        logger.warning(f"Intento de liberar más asientos de los reservados: reservados={av.reserved_seats}, liberar={qty}")
        qty = av.reserved_seats  # Liberar solo los que están reservados
    
    av.reserved_seats = max(0, av.reserved_seats - qty)
    av.save(update_fields=["reserved_seats"])
    
    logger.info(f"Liberados {qty} asientos en transporte {avail_id}. Restantes: {av.total_seats - av.reserved_seats}")
    return {
        'remaining': av.total_seats - av.reserved_seats,
        'reserved': av.reserved_seats,
        'total': av.total_seats
    }

@transaction.atomic
def reserve_room_availability(avail_id: int, qty: int):
    """
    Reserva `qty` habitaciones con validaciones mejoradas.
    """
    if qty <= 0:
        logger.warning(f"Intento de reservar cantidad inválida: {qty} (room_avail_id={avail_id})")
        raise InvalidQuantityError("La cantidad debe ser mayor a 0")
    
    try:
        av = RoomAvailability.objects.select_for_update().get(pk=avail_id)
    except ObjectDoesNotExist:
        raise ProductNotFoundError(f"Disponibilidad de habitación {avail_id} no encontrada")
    
    if av.available_quantity < qty:
        logger.warning(
            "Stock insuficiente (room_avail %s): solicitados %s, disponibles %s",
            avail_id, qty, av.available_quantity
        )
        raise InsufficientStockError(f"No hay habitaciones suficientes disponibles. Disponibles: {av.available_quantity}, Solicitadas: {qty}")
    
    # Validación adicional para evitar stock negativo
    if av.available_quantity - qty < 0:
        raise StockValidationError("La reserva resultaría en stock negativo")
    
    av.available_quantity -= qty
    av.save(update_fields=["available_quantity"])
    
    logger.info(f"Reservadas {qty} habitaciones en disponibilidad {avail_id}. Restantes: {av.available_quantity}")
    return {
        'remaining': av.available_quantity,
        'reserved': qty,
        'max_quantity': getattr(av, 'max_quantity', None)
    }

@transaction.atomic
def release_room_availability(avail_id: int, qty: int):
    """
    Libera `qty` habitaciones con validaciones mejoradas.
    """
    if qty <= 0:
        logger.warning(f"Intento de liberar cantidad inválida: {qty} (room_avail_id={avail_id})")
        raise InvalidQuantityError("La cantidad debe ser mayor a 0")
    
    try:
        av = RoomAvailability.objects.select_for_update().get(pk=avail_id)
    except ObjectDoesNotExist:
        raise ProductNotFoundError(f"Disponibilidad de habitación {avail_id} no encontrada")
    
    # Usar max_quantity si existe, sino calcular basado en available_quantity
    max_qty = getattr(av, "max_quantity", av.available_quantity + qty)
    new_quantity = min(max_qty, av.available_quantity + qty)
    
    av.available_quantity = new_quantity
    av.save(update_fields=["available_quantity"])
    
    logger.info(f"Liberadas {qty} habitaciones en disponibilidad {avail_id}. Restantes: {av.available_quantity}")
    return {
        'remaining': av.available_quantity,
        'released': qty,
        'max_quantity': max_qty
    }

@transaction.atomic
def reserve_flight(flight_id: int, qty: int):
    """
    Reserva `qty` asientos de un vuelo con validaciones mejoradas.
    """
    if qty <= 0:
        logger.warning(f"Intento de reservar cantidad inválida: {qty} (flight_id={flight_id})")
        raise InvalidQuantityError("La cantidad debe ser mayor a 0")
    
    try:
        flight = Flights.objects.select_for_update().get(pk=flight_id)
    except ObjectDoesNotExist:
        raise ProductNotFoundError(f"Vuelo {flight_id} no encontrado")
    
    if flight.available_seats < qty:
        logger.warning(
            "Stock insuficiente (flight %s): solicitados %s, disponibles %s",
            flight_id, qty, flight.available_seats
        )
        raise InsufficientStockError(f"No hay asientos suficientes en el vuelo. Disponibles: {flight.available_seats}, Solicitados: {qty}")
    
    # Validación adicional para evitar stock negativo
    if flight.available_seats - qty < 0:
        raise StockValidationError("La reserva resultaría en stock negativo")
    
    flight.available_seats -= qty
    flight.save(update_fields=["available_seats"])
    
    logger.info(f"Reservados {qty} asientos en vuelo {flight_id}. Restantes: {flight.available_seats}")
    return {
        'remaining': flight.available_seats,
        'reserved': qty,
        'capacity': getattr(flight, 'capacity', None)
    }

@transaction.atomic
def release_flight(flight_id: int, qty: int):
    """
    Libera `qty` asientos de un vuelo con validaciones mejoradas.
    """
    if qty <= 0:
        logger.warning(f"Intento de liberar cantidad inválida: {qty} (flight_id={flight_id})")
        raise InvalidQuantityError("La cantidad debe ser mayor a 0")
    
    try:
        flight = Flights.objects.select_for_update().get(pk=flight_id)
    except ObjectDoesNotExist:
        raise ProductNotFoundError(f"Vuelo {flight_id} no encontrado")
    
    # Usar capacity si existe, sino calcular basado en available_seats
    cap = getattr(flight, "capacity", flight.available_seats + qty)
    new_seats = min(cap, flight.available_seats + qty)
    
    flight.available_seats = new_seats
    flight.save(update_fields=["available_seats"])
    
    logger.info(f"Liberados {qty} asientos en vuelo {flight_id}. Restantes: {flight.available_seats}")
    return {
        'remaining': flight.available_seats,
        'released': qty,
        'capacity': cap
    }

# ─────────────────────────────────────────────
# FUNCIONES DE VALIDACIÓN BULK
# ─────────────────────────────────────────────

def validate_bulk_stock_reservation(reservations: list) -> dict:
    """
    Valida múltiples reservas de stock antes de ejecutarlas.
    Retorna un diccionario con el resultado de la validación.
    """
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'reservations': []
    }
    
    for reservation in reservations:
        try:
            product_type = reservation.get('type')
            product_id = reservation.get('id')
            quantity = reservation.get('quantity')
            
            if not all([product_type, product_id, quantity]):
                validation_results['errors'].append({
                    'reservation': reservation,
                    'error': 'Faltan campos requeridos (type, id, quantity)'
                })
                validation_results['valid'] = False
                continue
            
            if quantity <= 0:
                validation_results['errors'].append({
                    'reservation': reservation,
                    'error': 'La cantidad debe ser mayor a 0'
                })
                validation_results['valid'] = False
                continue
            
            # Validar stock según el tipo de producto
            if product_type == 'activity':
                stock_info = check_activity_stock(product_id, quantity)
            elif product_type == 'transportation':
                stock_info = check_transportation_stock(product_id, quantity)
            elif product_type == 'room':
                stock_info = check_room_stock(product_id, quantity)
            elif product_type == 'flight':
                stock_info = check_flight_stock(product_id, quantity)
            else:
                validation_results['errors'].append({
                    'reservation': reservation,
                    'error': f'Tipo de producto no válido: {product_type}'
                })
                validation_results['valid'] = False
                continue
            
            if not stock_info['sufficient']:
                validation_results['errors'].append({
                    'reservation': reservation,
                    'error': f'Stock insuficiente. Disponible: {stock_info["available"]}, Solicitado: {quantity}'
                })
                validation_results['valid'] = False
            else:
                validation_results['reservations'].append({
                    'reservation': reservation,
                    'stock_info': stock_info
                })
                
        except (InvalidQuantityError, ProductNotFoundError, InsufficientStockError) as e:
            validation_results['errors'].append({
                'reservation': reservation,
                'error': str(e)
            })
            validation_results['valid'] = False
        except Exception as e:
            validation_results['errors'].append({
                'reservation': reservation,
                'error': f'Error inesperado: {str(e)}'
            })
            validation_results['valid'] = False
    
    return validation_results

# ─────────────────────────────────────────────
# FUNCIONES DE UTILIDAD
# ─────────────────────────────────────────────

def get_stock_summary(product_type: str, product_id: int) -> dict:
    """
    Obtiene un resumen del stock actual de un producto.
    """
    try:
        if product_type == 'activity':
            av = ActivityAvailability.objects.get(pk=product_id)
            return {
                'type': 'activity',
                'id': product_id,
                'total': av.total_seats,
                'reserved': av.reserved_seats,
                'available': av.total_seats - av.reserved_seats,
                'utilization': round((av.reserved_seats / av.total_seats) * 100, 2) if av.total_seats > 0 else 0
            }
        elif product_type == 'transportation':
            av = TransportationAvailability.objects.get(pk=product_id)
            return {
                'type': 'transportation',
                'id': product_id,
                'total': av.total_seats,
                'reserved': av.reserved_seats,
                'available': av.total_seats - av.reserved_seats,
                'utilization': round((av.reserved_seats / av.total_seats) * 100, 2) if av.total_seats > 0 else 0
            }
        elif product_type == 'room':
            av = RoomAvailability.objects.get(pk=product_id)
            return {
                'type': 'room',
                'id': product_id,
                'available': av.available_quantity,
                'max_quantity': getattr(av, 'max_quantity', None),
                'utilization': 0  # Para habitaciones no aplica el mismo concepto
            }
        elif product_type == 'flight':
            flight = Flights.objects.get(pk=product_id)
            capacity = getattr(flight, 'capacity', flight.available_seats)
            return {
                'type': 'flight',
                'id': product_id,
                'capacity': capacity,
                'available': flight.available_seats,
                'reserved': capacity - flight.available_seats,
                'utilization': round(((capacity - flight.available_seats) / capacity) * 100, 2) if capacity > 0 else 0
            }
        else:
            raise ValueError(f"Tipo de producto no válido: {product_type}")
    except ObjectDoesNotExist:
        raise ProductNotFoundError(f"Producto {product_type} con ID {product_id} no encontrado") 