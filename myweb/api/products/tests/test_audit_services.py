import pytest
from datetime import date, time, timedelta, datetime
from decimal import Decimal
from django.test import TestCase, RequestFactory
from api.users.models import Users
from django.utils import timezone
from unittest.mock import Mock, patch
from api.products.models import (
    ActivityAvailability, TransportationAvailability, RoomAvailability, Flights,
    Activities, Transportation, Room, Lodgments, Location, Suppliers,
    StockAuditLog, StockChangeHistory, StockMetrics
)
from api.products.services.audit_services import (
    StockAuditService, StockAuditQueryService
)


class AuditServicesTestCase(TestCase):
    """Tests para los servicios de auditoría de stock."""
    
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
        
        # Crear alojamiento para tests de habitaciones
        self.lodgment = Lodgments.objects.create(
            name="Test Hotel",
            description="Test hotel description",
            location=self.location,
            type="hotel",
            max_guests=10,
            contact_phone="123456789",
            contact_email="hotel@test.com",
            date_checkin=date.today() + timedelta(days=1),
            date_checkout=date.today() + timedelta(days=3)
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
        
        # Crear usuario para tests
        self.user = Users.objects.create_user(
            email="test@example.com",
            password="testpass",
            first_name="Test",
            last_name="User",
            telephone="123456789"
        )
        
        # Crear request factory
        self.factory = RequestFactory()

    @pytest.mark.unit
    def test_get_request_context_with_request(self):
        """Test obtención de contexto de request con datos completos."""
        # Crear request mock
        request = Mock()
        request.user = self.user
        request.session = Mock()
        request.session.session_key = "test-session-123"
        request.request_id = "test-request-456"
        
        context = StockAuditService.get_request_context(request)
        
        self.assertEqual(context['user_id'], self.user.id)
        self.assertEqual(context['session_id'], "test-session-123")
        self.assertEqual(context['request_id'], "test-request-456")

    @pytest.mark.unit
    def test_get_request_context_without_request(self):
        """Test obtención de contexto sin request."""
        context = StockAuditService.get_request_context()
        
        self.assertIsNone(context['user_id'])
        self.assertIsNone(context['session_id'])
        self.assertIsNotNone(context['request_id'])  # Debería generar un UUID

    @pytest.mark.unit
    def test_get_request_context_anonymous_user(self):
        """Test obtención de contexto con usuario anónimo."""
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        request.session = Mock()
        request.session.session_key = "test-session-123"
        
        context = StockAuditService.get_request_context(request)
        
        self.assertIsNone(context['user_id'])
        self.assertEqual(context['session_id'], "test-session-123")

    @pytest.mark.unit
    def test_log_stock_operation_success(self):
        """Test logging exitoso de operación de stock."""
        log = StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=3,
            previous_stock=5,
            new_stock=8,
            user_id=self.user.id,
            success=True
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.operation_type, "reserve")
        self.assertEqual(log.product_type, "activity")
        self.assertEqual(log.product_id, self.activity_availability.id)
        self.assertEqual(log.quantity, 3)
        self.assertEqual(log.previous_stock, 5)
        self.assertEqual(log.new_stock, 8)
        self.assertEqual(log.user_id, self.user.id)
        self.assertTrue(log.success)
        self.assertEqual(log.error_message, "")

    @pytest.mark.unit
    def test_log_stock_operation_failure(self):
        """Test logging de operación fallida."""
        log = StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=25,
            success=False,
            error_message="Insufficient stock"
        )
        
        self.assertIsNotNone(log)
        self.assertFalse(log.success)
        self.assertEqual(log.error_message, "Insufficient stock")

    @pytest.mark.unit
    def test_log_stock_operation_with_metadata(self):
        """Test logging con metadatos."""
        metadata = {
            "source": "api",
            "ip_address": "127.0.0.1",
            "user_agent": "test-browser"
        }
        
        log = StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=2,
            metadata=metadata,
            success=True
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.metadata, metadata)

    @pytest.mark.unit
    def test_log_stock_change_increase(self):
        """Test logging de cambio de stock (aumento)."""
        # Crear log primero
        audit_log = StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=3,
            success=True
        )
        
        # Registrar cambio
        change = StockAuditService.log_stock_change(
            audit_log=audit_log,
            field_name="reserved_seats",
            old_value=5,
            new_value=8
        )
        
        self.assertIsNotNone(change)
        self.assertEqual(change.audit_log, audit_log)
        self.assertEqual(change.field_name, "reserved_seats")
        self.assertEqual(change.old_value, 5)
        self.assertEqual(change.new_value, 8)
        self.assertEqual(change.change_type, "increase")
        self.assertEqual(change.change_amount, 3)

    @pytest.mark.unit
    def test_log_stock_change_decrease(self):
        """Test logging de cambio de stock (disminución)."""
        audit_log = StockAuditService.log_stock_operation(
            operation_type="release",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=2,
            success=True
        )
        
        change = StockAuditService.log_stock_change(
            audit_log=audit_log,
            field_name="reserved_seats",
            old_value=8,
            new_value=6
        )
        
        self.assertIsNotNone(change)
        self.assertEqual(change.change_type, "decrease")
        self.assertEqual(change.change_amount, -2)

    @pytest.mark.unit
    def test_log_stock_change_no_change(self):
        """Test logging cuando no hay cambio."""
        audit_log = StockAuditService.log_stock_operation(
            operation_type="check",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=0,
            success=True
        )
        
        change = StockAuditService.log_stock_change(
            audit_log=audit_log,
            field_name="reserved_seats",
            old_value=5,
            new_value=5
        )
        
        self.assertIsNone(change)  # No debería crear registro

    @pytest.mark.unit
    def test_update_stock_metrics_new(self):
        """Test actualización de métricas (nuevas)."""
        metrics = StockAuditService.update_stock_metrics(
            product_type="activity",
            product_id=self.activity_availability.id,
            total_capacity=20,
            current_reserved=8,
            current_available=12,
            as_of_date=timezone.now().date()
        )
        
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.product_type, "activity")
        self.assertEqual(metrics.product_id, self.activity_availability.id)
        self.assertEqual(metrics.total_capacity, 20)
        self.assertEqual(metrics.current_reserved, 8)
        self.assertEqual(metrics.current_available, 12)
        self.assertEqual(metrics.utilization_rate, 40.0)  # 8/20 * 100

    @pytest.mark.unit
    def test_update_stock_metrics_existing(self):
        """Test actualización de métricas existentes."""
        # Crear métricas iniciales
        initial_metrics = StockAuditService.update_stock_metrics(
            product_type="activity",
            product_id=self.activity_availability.id,
            total_capacity=20,
            current_reserved=5,
            current_available=15,
            as_of_date=timezone.now().date()
        )
        
        # Actualizar las mismas métricas
        updated_metrics = StockAuditService.update_stock_metrics(
            product_type="activity",
            product_id=self.activity_availability.id,
            total_capacity=20,
            current_reserved=10,
            current_available=10,
            as_of_date=timezone.now().date()
        )
        
        self.assertEqual(updated_metrics.id, initial_metrics.id)
        self.assertEqual(updated_metrics.current_reserved, 10)
        self.assertEqual(updated_metrics.utilization_rate, 50.0)  # 10/20 * 100

    @pytest.mark.unit
    def test_log_activity_stock_operation(self):
        """Test logging específico de operaciones de actividad."""
        log = StockAuditService.log_activity_stock_operation(
            operation_type="reserve",
            availability_id=self.activity_availability.id,
            quantity=3,
            previous_reserved=5,
            new_reserved=8,
            success=True
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.operation_type, "reserve")
        self.assertEqual(log.product_type, "activity")
        self.assertEqual(log.product_id, self.activity_availability.id)
        self.assertEqual(log.quantity, 3)
        self.assertEqual(log.previous_stock, 5)
        self.assertEqual(log.new_stock, 8)
        self.assertTrue(log.success)

    @pytest.mark.unit
    def test_log_transportation_stock_operation(self):
        """Test logging específico de operaciones de transporte."""
        log = StockAuditService.log_transportation_stock_operation(
            operation_type="reserve",
            availability_id=self.transportation_availability.id,
            quantity=5,
            previous_reserved=10,
            new_reserved=15,
            success=True
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.operation_type, "reserve")
        self.assertEqual(log.product_type, "transportation")
        self.assertEqual(log.product_id, self.transportation_availability.id)
        self.assertEqual(log.quantity, 5)
        self.assertEqual(log.previous_stock, 10)
        self.assertEqual(log.new_stock, 15)
        self.assertTrue(log.success)

    @pytest.mark.unit
    def test_log_room_stock_operation(self):
        """Test logging específico de operaciones de habitaciones."""
        log = StockAuditService.log_room_stock_operation(
            operation_type="reserve",
            availability_id=self.room_availability.id,
            quantity=2,
            previous_available=5,
            new_available=3,
            success=True
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.operation_type, "reserve")
        self.assertEqual(log.product_type, "room")
        self.assertEqual(log.product_id, self.room_availability.id)
        self.assertEqual(log.quantity, 2)
        self.assertEqual(log.previous_stock, 5)
        self.assertEqual(log.new_stock, 3)
        self.assertTrue(log.success)

    @pytest.mark.unit
    def test_log_flight_stock_operation(self):
        """Test logging específico de operaciones de vuelos."""
        log = StockAuditService.log_flight_stock_operation(
            operation_type="reserve",
            flight_id=self.flight.id,
            quantity=3,
            previous_available=50,
            new_available=47,
            success=True
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.operation_type, "reserve")
        self.assertEqual(log.product_type, "flight")
        self.assertEqual(log.product_id, self.flight.id)
        self.assertEqual(log.quantity, 3)
        self.assertEqual(log.previous_stock, 50)
        self.assertEqual(log.new_stock, 47)
        self.assertTrue(log.success)

    @pytest.mark.unit
    def test_get_audit_logs_basic(self):
        """Test obtención básica de logs de auditoría."""
        # Crear algunos logs
        for i in range(3):
            StockAuditService.log_stock_operation(
                operation_type="reserve",
                product_type="activity",
                product_id=self.activity_availability.id,
                quantity=1,
                success=True
            )
        
        logs = StockAuditQueryService.get_audit_logs(
            product_type="activity",
            product_id=self.activity_availability.id
        )
        
        self.assertEqual(len(logs), 3)
        for log in logs:
            self.assertEqual(log.product_type, "activity")
            self.assertEqual(log.product_id, self.activity_availability.id)

    @pytest.mark.unit
    def test_get_audit_logs_with_filters(self):
        """Test obtención de logs con filtros."""
        # Crear logs exitosos y fallidos
        StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=1,
            success=True
        )
        
        StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=20,
            success=False
        )
        
        # Filtrar solo exitosos
        success_logs = StockAuditQueryService.get_audit_logs(
            product_type="activity",
            success_only=True
        )
        
        self.assertEqual(len(success_logs), 1)
        self.assertTrue(success_logs[0].success)
        
        # Filtrar por tipo de operación
        reserve_logs = StockAuditQueryService.get_audit_logs(
            product_type="activity",
            operation_type="reserve"
        )
        
        self.assertEqual(len(reserve_logs), 2)
        for log in reserve_logs:
            self.assertEqual(log.operation_type, "reserve")

    @pytest.mark.unit
    def test_get_audit_logs_with_date_filters(self):
        """Test obtención de logs con filtros de fecha."""
        # Crear logs en diferentes fechas
        yesterday = timezone.now() - timedelta(days=1)
        today = timezone.now()
        
        with patch('django.utils.timezone.now', return_value=yesterday):
            StockAuditService.log_stock_operation(
                operation_type="reserve",
                product_type="activity",
                product_id=self.activity_availability.id,
                quantity=1,
                success=True
            )
        
        with patch('django.utils.timezone.now', return_value=today):
            StockAuditService.log_stock_operation(
                operation_type="reserve",
                product_type="activity",
                product_id=self.activity_availability.id,
                quantity=1,
                success=True
            )
        
        # Filtrar por fecha
        today_logs = StockAuditQueryService.get_audit_logs(
            product_type="activity",
            start_date=today
        )
        
        self.assertGreaterEqual(len(today_logs), 1)

    @pytest.mark.unit
    def test_get_stock_changes(self):
        """Test obtención de cambios de stock."""
        # Crear log y cambios
        audit_log = StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=3,
            success=True
        )
        
        StockAuditService.log_stock_change(
            audit_log=audit_log,
            field_name="reserved_seats",
            old_value=5,
            new_value=8
        )
        
        changes = StockAuditQueryService.get_stock_changes(
            audit_log_id=audit_log.id
        )
        
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].field_name, "reserved_seats")
        self.assertEqual(changes[0].old_value, 5)
        self.assertEqual(changes[0].new_value, 8)

    @pytest.mark.unit
    def test_get_stock_metrics(self):
        """Test obtención de métricas de stock."""
        # Crear métricas
        StockAuditService.update_stock_metrics(
            product_type="activity",
            product_id=self.activity_availability.id,
            total_capacity=20,
            current_reserved=8,
            current_available=12,
            as_of_date=timezone.now().date()
        )
        
        metrics = StockAuditQueryService.get_stock_metrics(
            product_type="activity",
            product_id=self.activity_availability.id
        )
        
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0].product_type, "activity")
        self.assertEqual(metrics[0].product_id, self.activity_availability.id)
        self.assertEqual(metrics[0].total_capacity, 20)
        self.assertEqual(metrics[0].current_reserved, 8)

    @pytest.mark.unit
    def test_get_operation_summary(self):
        """Test obtención de resumen de operaciones."""
        # Crear operaciones exitosas y fallidas
        for i in range(3):
            StockAuditService.log_stock_operation(
                operation_type="reserve",
                product_type="activity",
                product_id=self.activity_availability.id,
                quantity=1,
                success=True
            )
        
        StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=20,
            success=False
        )
        
        summary = StockAuditQueryService.get_operation_summary(
            product_type="activity",
            product_id=self.activity_availability.id
        )
        
        self.assertIsNotNone(summary)
        self.assertIn('total_operations', summary)
        self.assertIn('successful_operations', summary)
        self.assertIn('failed_operations', summary)
        self.assertIn('success_rate', summary)
        
        self.assertEqual(summary['total_operations'], 4)
        self.assertEqual(summary['successful_operations'], 3)
        self.assertEqual(summary['failed_operations'], 1)
        self.assertEqual(summary['success_rate'], 75.0)  # 3/4 * 100

    @pytest.mark.unit
    def test_get_operation_summary_with_date_filters(self):
        """Test resumen de operaciones con filtros de fecha."""
        # Crear operaciones en diferentes fechas
        yesterday = timezone.now() - timedelta(days=1)
        today = timezone.now()
        
        with patch('django.utils.timezone.now', return_value=yesterday):
            StockAuditService.log_stock_operation(
                operation_type="reserve",
                product_type="activity",
                product_id=self.activity_availability.id,
                quantity=1,
                success=True
            )
        
        with patch('django.utils.timezone.now', return_value=today):
            StockAuditService.log_stock_operation(
                operation_type="reserve",
                product_type="activity",
                product_id=self.activity_availability.id,
                quantity=1,
                success=True
            )
        
        # Resumen solo de hoy
        today_summary = StockAuditQueryService.get_operation_summary(
            product_type="activity",
            product_id=self.activity_availability.id,
            start_date=today
        )
        
        self.assertIsNotNone(today_summary)
        self.assertGreaterEqual(today_summary['total_operations'], 1)

    @pytest.mark.unit
    def test_error_handling_in_log_stock_operation(self):
        """Test manejo de errores en logging de operaciones."""
        # Simular error en la creación del log
        with patch('api.products.models.StockAuditLog.log_operation', side_effect=Exception("Database error")):
            result = StockAuditService.log_stock_operation(
                operation_type="reserve",
                product_type="activity",
                product_id=self.activity_availability.id,
                quantity=1,
                success=True
            )
            
            # Debería retornar None en lugar de lanzar excepción
            self.assertIsNone(result)

    @pytest.mark.unit
    def test_error_handling_in_log_stock_change(self):
        """Test manejo de errores en logging de cambios."""
        audit_log = StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=1,
            success=True
        )
        
        # Simular error en la creación del cambio
        with patch('api.products.models.StockChangeHistory.log_change', side_effect=Exception("Database error")):
            result = StockAuditService.log_stock_change(
                audit_log=audit_log,
                field_name="reserved_seats",
                old_value=5,
                new_value=6
            )
            
            # Debería retornar None en lugar de lanzar excepción
            self.assertIsNone(result)

    @pytest.mark.unit
    def test_metrics_calculation_from_logs(self):
        """Test cálculo de métricas basado en logs."""
        # Crear logs de diferentes tipos
        StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=2,
            success=True
        )
        
        StockAuditService.log_stock_operation(
            operation_type="release",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=1,
            success=True
        )
        
        StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=20,
            success=False
        )
        
        # Actualizar métricas
        metrics = StockAuditService.update_stock_metrics(
            product_type="activity",
            product_id=self.activity_availability.id,
            total_capacity=20,
            current_reserved=6,
            current_available=14,
            as_of_date=timezone.now().date()
        )
        
        # Verificar que los contadores coinciden con los logs
        self.assertEqual(metrics.total_reservations, 1)  # Solo 1 reserva exitosa
        self.assertEqual(metrics.total_releases, 1)      # 1 liberación exitosa
        self.assertEqual(metrics.failed_operations, 1)   # 1 operación fallida

    @pytest.mark.unit
    def test_utilization_rate_calculation(self):
        """Test cálculo de tasa de utilización."""
        # Caso: utilización del 50%
        metrics = StockAuditService.update_stock_metrics(
            product_type="activity",
            product_id=self.activity_availability.id,
            total_capacity=20,
            current_reserved=10,
            current_available=10,
            as_of_date=timezone.now().date()
        )
        
        self.assertEqual(metrics.utilization_rate, 50.0)  # 10/20 * 100
        
        # Caso: utilización del 0%
        metrics_zero = StockAuditService.update_stock_metrics(
            product_type="activity",
            product_id=self.activity_availability.id,
            total_capacity=20,
            current_reserved=0,
            current_available=20,
            as_of_date=timezone.now().date()
        )
        
        self.assertEqual(metrics_zero.utilization_rate, 0.0)
        
        # Caso: utilización del 100%
        metrics_full = StockAuditService.update_stock_metrics(
            product_type="activity",
            product_id=self.activity_availability.id,
            total_capacity=20,
            current_reserved=20,
            current_available=0,
            as_of_date=timezone.now().date()
        )
        
        self.assertEqual(metrics_full.utilization_rate, 100.0)

    @pytest.mark.unit
    def test_metrics_with_zero_capacity(self):
        """Test métricas con capacidad cero."""
        metrics = StockAuditService.update_stock_metrics(
            product_type="activity",
            product_id=self.activity_availability.id,
            total_capacity=0,
            current_reserved=0,
            current_available=0,
            as_of_date=timezone.now().date()
        )
        
        self.assertEqual(metrics.utilization_rate, 0.0)  # Debería manejar división por cero 