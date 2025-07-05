import pytest
from datetime import date, time, timedelta
from decimal import Decimal
from django.test import TestCase
from api.products.models import (
    ActivityAvailability, TransportationAvailability, RoomAvailability, Flights,
    Activities, Transportation, Room, Lodgments, Location, Suppliers
)
from api.products.services.stock_services import (
    check_activity_stock, check_transportation_stock, check_room_stock, check_flight_stock,
    reserve_activity, release_activity, reserve_transportation, release_transportation,
    reserve_room_availability, release_room_availability, reserve_flight, release_flight,
    validate_bulk_stock_reservation, get_stock_summary,
    InsufficientStockError, InvalidQuantityError, ProductNotFoundError, StockValidationError
)


class StockServicesTestCase(TestCase):
    """Pruebas para los servicios de stock mejorados."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Crear ubicación
        self.location = Location.objects.create(
            name="Test City",
            country="Test Country",
            state="Test State",
            city="Test City",
            type="city"
        )
        
        # Crear proveedor
        self.supplier = Suppliers.objects.create(
            first_name="Test",
            last_name="Supplier",
            organization_name="Test Org",
            description="Test supplier",
            street="Test Street",
            street_number=123,
            city="Test City",
            country="Test Country",
            email="test@example.com",
            telephone="123456789",
            website="https://test.com"
        )
        
        # Crear actividad
        self.activity = Activities.objects.create(
            name="Test Activity",
            description="Test activity description",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="English",
            available_slots=20
        )
        
        # Crear disponibilidad de actividad
        self.activity_availability = ActivityAvailability.objects.create(
            activity=self.activity,
            event_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            total_seats=20,
            reserved_seats=5,
            price=Decimal("100.00"),
            currency="USD",
            state="active"
        )
        
        # Crear transporte
        self.transportation = Transportation.objects.create(
            origin=self.location,
            destination=self.location,
            type="bus",
            description="Test transportation",
            capacity=30
        )
        
        # Crear disponibilidad de transporte
        self.transportation_availability = TransportationAvailability.objects.create(
            transportation=self.transportation,
            departure_date=date.today() + timedelta(days=5),
            departure_time=time(8, 0),
            arrival_date=date.today() + timedelta(days=5),
            arrival_time=time(10, 0),
            total_seats=30,
            reserved_seats=10,
            price=Decimal("50.00"),
            currency="USD",
            state="active"
        )
        
        # Crear alojamiento
        self.lodgment = Lodgments.objects.create(
            name="Test Hotel",
            description="Test hotel description",
            location=self.location,
            type="hotel",
            max_guests=10,
            date_checkin=date.today() + timedelta(days=3),
            date_checkout=date.today() + timedelta(days=5)
        )
        
        # Crear habitación
        self.room = Room.objects.create(
            lodgment=self.lodgment,
            room_type="double",
            name="Test Room",
            capacity=2,
            base_price_per_night=Decimal("80.00"),
            currency="USD"
        )
        
        # Crear disponibilidad de habitación
        self.room_availability = RoomAvailability.objects.create(
            room=self.room,
            start_date=date.today() + timedelta(days=3),
            end_date=date.today() + timedelta(days=5),
            available_quantity=5,
            max_quantity=5,
            currency="USD",
            is_blocked=False,
            minimum_stay=1
        )
        
        # Crear vuelo
        self.flight = Flights.objects.create(
            airline="Test Airline",
            flight_number="TA123",
            origin=self.location,
            destination=self.location,
            departure_date=date.today() + timedelta(days=2),
            arrival_date=date.today() + timedelta(days=2),
            duration_hours=2,
            departure_time=time(14, 0),
            arrival_time=time(16, 0),
            class_flight="Economy",
            available_seats=50,
            capacity=50,
            luggage_info="1 checked bag",
            aircraft_type="Boeing 737"
        )

    def test_check_activity_stock_sufficient(self):
        """Prueba verificación de stock suficiente para actividad."""
        result = check_activity_stock(self.activity_availability.id, 10)
        
        self.assertTrue(result['sufficient'])
        self.assertEqual(result['available'], 15)  # 20 total - 5 reservados
        self.assertEqual(result['requested'], 10)
        self.assertEqual(result['total_seats'], 20)
        self.assertEqual(result['reserved_seats'], 5)

    def test_check_activity_stock_insufficient(self):
        """Prueba verificación de stock insuficiente para actividad."""
        result = check_activity_stock(self.activity_availability.id, 20)
        
        self.assertFalse(result['sufficient'])
        self.assertEqual(result['available'], 15)
        self.assertEqual(result['requested'], 20)

    def test_check_activity_stock_invalid_quantity(self):
        """Prueba verificación con cantidad inválida."""
        with self.assertRaises(InvalidQuantityError):
            check_activity_stock(self.activity_availability.id, 0)
        
        with self.assertRaises(InvalidQuantityError):
            check_activity_stock(self.activity_availability.id, -5)

    def test_check_activity_stock_product_not_found(self):
        """Prueba verificación con ID inexistente."""
        with self.assertRaises(ProductNotFoundError):
            check_activity_stock(99999, 10)

    def test_reserve_activity_success(self):
        """Prueba reserva exitosa de actividad."""
        result = reserve_activity(self.activity_availability.id, 5)
        
        self.assertEqual(result['remaining'], 10)  # 20 total - 10 reservados
        self.assertEqual(result['reserved'], 10)   # 5 originales + 5 nuevos
        self.assertEqual(result['total'], 20)
        
        # Verificar que se actualizó en la base de datos
        self.activity_availability.refresh_from_db()
        self.assertEqual(self.activity_availability.reserved_seats, 10)

    def test_reserve_activity_insufficient_stock(self):
        """Prueba reserva con stock insuficiente."""
        with self.assertRaises(InsufficientStockError):
            reserve_activity(self.activity_availability.id, 20)

    def test_reserve_activity_invalid_quantity(self):
        """Prueba reserva con cantidad inválida."""
        with self.assertRaises(InvalidQuantityError):
            reserve_activity(self.activity_availability.id, 0)

    def test_release_activity_success(self):
        """Prueba liberación exitosa de actividad."""
        # Primero reservar algunos asientos
        reserve_activity(self.activity_availability.id, 3)
        
        # Luego liberar algunos
        result = release_activity(self.activity_availability.id, 2)
        
        self.assertEqual(result['remaining'], 14)  # 20 total - 6 reservados
        self.assertEqual(result['reserved'], 6)    # 5 originales + 3 - 2
        self.assertEqual(result['total'], 20)

    def test_release_activity_more_than_reserved(self):
        """Prueba liberación de más asientos de los reservados."""
        # Intentar liberar más de los reservados
        result = release_activity(self.activity_availability.id, 10)
        
        # Debería liberar solo los 5 que están reservados
        self.assertEqual(result['remaining'], 20)  # Todos liberados
        self.assertEqual(result['reserved'], 0)    # Ninguno reservado

    def test_check_transportation_stock(self):
        """Prueba verificación de stock de transporte."""
        result = check_transportation_stock(self.transportation_availability.id, 15)
        
        self.assertTrue(result['sufficient'])
        self.assertEqual(result['available'], 20)  # 30 total - 10 reservados

    def test_reserve_transportation_success(self):
        """Prueba reserva exitosa de transporte."""
        result = reserve_transportation(self.transportation_availability.id, 10)
        
        self.assertEqual(result['remaining'], 10)  # 30 total - 20 reservados
        self.assertEqual(result['reserved'], 20)   # 10 originales + 10 nuevos

    def test_check_room_stock(self):
        """Prueba verificación de stock de habitaciones."""
        result = check_room_stock(self.room_availability.id, 3)
        
        self.assertTrue(result['sufficient'])
        self.assertEqual(result['available'], 5)

    def test_reserve_room_success(self):
        """Prueba reserva exitosa de habitaciones."""
        result = reserve_room_availability(self.room_availability.id, 2)
        
        self.assertEqual(result['remaining'], 3)  # 5 disponibles - 2 reservadas
        self.assertEqual(result['reserved'], 2)

    def test_check_flight_stock(self):
        """Prueba verificación de stock de vuelo."""
        result = check_flight_stock(self.flight.id, 30)
        
        self.assertTrue(result['sufficient'])
        self.assertEqual(result['available'], 50)

    def test_reserve_flight_success(self):
        """Prueba reserva exitosa de vuelo."""
        result = reserve_flight(self.flight.id, 20)
        
        self.assertEqual(result['remaining'], 30)  # 50 disponibles - 20 reservados
        self.assertEqual(result['reserved'], 20)

    def test_validate_bulk_stock_reservation_success(self):
        """Prueba validación bulk exitosa."""
        reservations = [
            {'type': 'activity', 'id': self.activity_availability.id, 'quantity': 5},
            {'type': 'transportation', 'id': self.transportation_availability.id, 'quantity': 10},
            {'type': 'room', 'id': self.room_availability.id, 'quantity': 2},
            {'type': 'flight', 'id': self.flight.id, 'quantity': 15}
        ]
        
        result = validate_bulk_stock_reservation(reservations)
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(len(result['reservations']), 4)

    def test_validate_bulk_stock_reservation_with_errors(self):
        """Prueba validación bulk con errores."""
        reservations = [
            {'type': 'activity', 'id': self.activity_availability.id, 'quantity': 5},
            {'type': 'activity', 'id': self.activity_availability.id, 'quantity': 20},  # Stock insuficiente
            {'type': 'invalid_type', 'id': 1, 'quantity': 1},  # Tipo inválido
            {'type': 'activity', 'id': 99999, 'quantity': 1}   # ID inexistente
        ]
        
        result = validate_bulk_stock_reservation(reservations)
        
        self.assertFalse(result['valid'])
        self.assertEqual(len(result['errors']), 3)
        self.assertEqual(len(result['reservations']), 1)

    def test_get_stock_summary_activity(self):
        """Prueba obtención de resumen de stock para actividad."""
        summary = get_stock_summary('activity', self.activity_availability.id)
        
        self.assertEqual(summary['type'], 'activity')
        self.assertEqual(summary['total'], 20)
        self.assertEqual(summary['reserved'], 5)
        self.assertEqual(summary['available'], 15)
        self.assertEqual(summary['utilization'], 25.0)  # 5/20 * 100

    def test_get_stock_summary_transportation(self):
        """Prueba obtención de resumen de stock para transporte."""
        summary = get_stock_summary('transportation', self.transportation_availability.id)
        
        self.assertEqual(summary['type'], 'transportation')
        self.assertEqual(summary['total'], 30)
        self.assertEqual(summary['reserved'], 10)
        self.assertEqual(summary['available'], 20)
        self.assertEqual(summary['utilization'], 33.33)  # 10/30 * 100

    def test_get_stock_summary_room(self):
        """Prueba obtención de resumen de stock para habitación."""
        summary = get_stock_summary('room', self.room_availability.id)
        
        self.assertEqual(summary['type'], 'room')
        self.assertEqual(summary['available'], 5)
        self.assertEqual(summary['max_quantity'], 5)

    def test_get_stock_summary_flight(self):
        """Prueba obtención de resumen de stock para vuelo."""
        summary = get_stock_summary('flight', self.flight.id)
        
        self.assertEqual(summary['type'], 'flight')
        self.assertEqual(summary['capacity'], 50)
        self.assertEqual(summary['available'], 50)
        self.assertEqual(summary['reserved'], 0)
        self.assertEqual(summary['utilization'], 0.0)

    def test_get_stock_summary_invalid_type(self):
        """Prueba obtención de resumen con tipo inválido."""
        with self.assertRaises(ValueError):
            get_stock_summary('invalid_type', 1)

    def test_get_stock_summary_product_not_found(self):
        """Prueba obtención de resumen con producto inexistente."""
        with self.assertRaises(ProductNotFoundError):
            get_stock_summary('activity', 99999)

    def test_concurrent_reservations(self):
        """Prueba reservas secuenciales para verificar integridad de datos."""
        # Resetear el stock para esta prueba
        self.activity_availability.reserved_seats = 0
        self.activity_availability.save()
        
        # Realizar múltiples reservas secuenciales para verificar integridad
        for i in range(5):
            result = reserve_activity(self.activity_availability.id, 1)
            self.assertEqual(result['reserved'], i + 1)
            self.assertEqual(result['remaining'], 19 - i)
        
        # Verificar estado final
        self.activity_availability.refresh_from_db()
        total_reserved = self.activity_availability.reserved_seats
        
        # Verificar que se realizaron todas las reservas
        self.assertEqual(total_reserved, 5)
        
        # Verificar que no hay más reservas que asientos totales
        self.assertLessEqual(total_reserved, self.activity_availability.total_seats)
        
        # Verificar que no se puede reservar más de lo disponible
        with self.assertRaises(InsufficientStockError):
            reserve_activity(self.activity_availability.id, 16)  # Solo quedan 15 disponibles

    def test_stock_validation_edge_cases(self):
        """Prueba casos límite de validación de stock."""
        # Caso: cantidad exacta disponible
        result = check_activity_stock(self.activity_availability.id, 15)
        self.assertTrue(result['sufficient'])
        
        # Caso: cantidad mayor a disponible
        result = check_activity_stock(self.activity_availability.id, 16)
        self.assertFalse(result['sufficient'])
        
        # Caso: cantidad cero
        with self.assertRaises(InvalidQuantityError):
            check_activity_stock(self.activity_availability.id, 0)
        
        # Caso: cantidad negativa
        with self.assertRaises(InvalidQuantityError):
            check_activity_stock(self.activity_availability.id, -1)

    def test_stock_release_edge_cases(self):
        """Prueba casos límite de liberación de stock."""
        # Caso: liberar más de lo reservado
        result = release_activity(self.activity_availability.id, 10)
        self.assertEqual(result['reserved'], 0)
        
        # Caso: liberar cantidad exacta
        self.activity_availability.reserved_seats = 5
        self.activity_availability.save()
        
        result = release_activity(self.activity_availability.id, 5)
        self.assertEqual(result['reserved'], 0)
        
        # Caso: liberar cantidad cero
        with self.assertRaises(InvalidQuantityError):
            release_activity(self.activity_availability.id, 0)
        
        # Caso: liberar cantidad negativa
        with self.assertRaises(InvalidQuantityError):
            release_activity(self.activity_availability.id, -1) 