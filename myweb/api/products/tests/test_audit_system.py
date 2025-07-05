import pytest
from datetime import date, time, timedelta, datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from api.products.models import (
    ActivityAvailability, TransportationAvailability, RoomAvailability, Flights,
    Activities, Transportation, Room, Lodgments, Location, Suppliers,
    StockAuditLog, StockChangeHistory, StockMetrics
)
from api.products.services.audit_services import (
    StockAuditService, StockAuditQueryService
)
from api.products.services.stock_services import (
    reserve_activity, release_activity, check_activity_stock,
    InsufficientStockError, InvalidQuantityError, ProductNotFoundError
)


class AuditSystemTestCase(TestCase):
    """Test general del sistema de auditoría de stock."""
    
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
        from api.products.models import Lodgments
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

    def test_audit_log_creation(self):
        """Prueba creación básica de logs de auditoría."""
        # Crear un log manual
        log = StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=3,
            previous_stock=5,
            new_stock=8,
            user_id=1,
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
        self.assertIsNotNone(log.created_at)

    def test_audit_log_with_metadata(self):
        """Prueba logs de auditoría con metadatos."""
        metadata = {
            "user_agent": "test-browser",
            "ip_address": "127.0.0.1",
            "session_id": "test-session-123"
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

    def test_audit_log_failed_operation(self):
        """Prueba logs de auditoría para operaciones fallidas."""
        log = StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=25,  # Más de lo disponible
            success=False,
            error_message="Insufficient stock available"
        )
        
        self.assertIsNotNone(log)
        self.assertFalse(log.success)
        self.assertEqual(log.error_message, "Insufficient stock available")

    def test_stock_change_logging(self):
        """Prueba registro de cambios específicos de stock."""
        # Crear un log primero
        audit_log = StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=3,
            previous_stock=5,
            new_stock=8,
            success=True
        )
        
        # Registrar el cambio específico
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

    def test_stock_metrics_creation(self):
        """Prueba creación de métricas de stock."""
        # Crear algunos logs primero
        for i in range(3):
            StockAuditService.log_stock_operation(
                operation_type="reserve",
                product_type="activity",
                product_id=self.activity_availability.id,
                quantity=1,
                success=True
            )
        
        # Crear métricas
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
        self.assertGreaterEqual(metrics.total_reservations, 3)

    def test_activity_stock_operation_logging(self):
        """Prueba logging específico de operaciones de actividad."""
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

    def test_stock_services_with_audit(self):
        """Prueba que los servicios de stock registren auditoría."""
        # Verificar stock antes
        check_result = check_activity_stock(self.activity_availability.id, 3)
        self.assertTrue(check_result['sufficient'])
        
        # Reservar con auditoría
        result = reserve_activity(self.activity_availability.id, 3)
        
        self.assertEqual(result['remaining'], 12)  # 20 total - 8 reservados
        self.assertEqual(result['reserved'], 8)    # 5 originales + 3 nuevos
        
        # Verificar que se creó el log
        logs = StockAuditLog.objects.filter(
            product_type="activity",
            product_id=self.activity_availability.id,
            operation_type="reserve"
        )
        self.assertGreater(logs.count(), 0)
        
        # Verificar que se actualizaron las métricas
        metrics = StockMetrics.objects.filter(
            product_type="activity",
            product_id=self.activity_availability.id
        ).first()
        self.assertIsNotNone(metrics)

    def test_audit_query_service(self):
        """Prueba el servicio de consulta de auditoría."""
        # Crear varios logs
        for i in range(5):
            StockAuditService.log_stock_operation(
                operation_type="reserve",
                product_type="activity",
                product_id=self.activity_availability.id,
                quantity=1,
                user_id=1,
                success=True
            )
        
        # Consultar logs
        logs = StockAuditQueryService.get_audit_logs(
            product_type="activity",
            product_id=self.activity_availability.id,
            operation_type="reserve",
            success_only=True
        )
        
        self.assertGreater(len(logs), 0)
        for log in logs:
            self.assertEqual(log.product_type, "activity")
            self.assertEqual(log.product_id, self.activity_availability.id)
            self.assertEqual(log.operation_type, "reserve")
            self.assertTrue(log.success)

    def test_operation_summary(self):
        """Prueba resumen de operaciones."""
        # Crear logs exitosos y fallidos
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
            success=False,
            error_message="Insufficient stock"
        )
        
        # Obtener resumen
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

    def test_error_handling_in_audit(self):
        """Prueba manejo de errores en auditoría."""
        # Crear un log de error manual para verificar que funciona
        manual_log = StockAuditService.log_activity_stock_operation(
            operation_type="reserve",
            availability_id=self.activity_availability.id,
            quantity=20,
            success=False,
            error_message="Test error message"
        )
        
        # Verificar que se creó el log manual
        self.assertIsNotNone(manual_log)
        self.assertFalse(manual_log.success)
        
        # Ahora probar con la función que falla
        # Usar try/except en lugar de assertRaises para evitar que la transacción se revierta
        try:
            reserve_activity(self.activity_availability.id, 20)
            self.fail("Debería haber lanzado InsufficientStockError")
        except InsufficientStockError:
            # La excepción se lanzó correctamente, ahora verificar el log
            pass
        
        # Verificar que se registró el error en auditoría
        error_logs = StockAuditLog.objects.filter(
            product_type="activity",
            product_id=self.activity_availability.id,
            success=False
        )
        
        # Debería haber al menos 2 logs de error (el manual + el de la función)
        self.assertGreaterEqual(error_logs.count(), 2)
        
        # Verificar que se creó el log de la función
        function_error_log = error_logs.filter(
            error_message__contains="No hay asientos suficientes"
        ).first()
        self.assertIsNotNone(function_error_log)
        self.assertEqual(function_error_log.operation_type, "reserve")
        self.assertEqual(function_error_log.quantity, 20)
        self.assertFalse(function_error_log.success)
        self.assertIn("No hay asientos suficientes", function_error_log.error_message)

    def test_audit_log_ordering(self):
        """Prueba ordenamiento de logs de auditoría."""
        # Crear logs con diferentes timestamps
        for i in range(3):
            StockAuditService.log_stock_operation(
                operation_type="reserve",
                product_type="activity",
                product_id=self.activity_availability.id,
                quantity=1,
                success=True
            )
        
        # Consultar ordenados por fecha descendente
        logs = StockAuditQueryService.get_audit_logs(
            product_type="activity",
            limit=10
        )
        
        # Verificar que están ordenados (más recientes primero)
        if len(logs) > 1:
            for i in range(len(logs) - 1):
                self.assertGreaterEqual(logs[i].created_at, logs[i + 1].created_at)

    def test_audit_log_filtering(self):
        """Prueba filtrado de logs de auditoría."""
        # Crear logs con diferentes tipos de operación
        StockAuditService.log_stock_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=1,
            success=True
        )
        
        StockAuditService.log_stock_operation(
            operation_type="release",
            product_type="activity",
            product_id=self.activity_availability.id,
            quantity=1,
            success=True
        )
        
        # Filtrar por tipo de operación
        reserve_logs = StockAuditQueryService.get_audit_logs(
            product_type="activity",
            operation_type="reserve"
        )
        
        release_logs = StockAuditQueryService.get_audit_logs(
            product_type="activity",
            operation_type="release"
        )
        
        self.assertEqual(len(reserve_logs), 1)
        self.assertEqual(len(release_logs), 1)
        self.assertEqual(reserve_logs[0].operation_type, "reserve")
        self.assertEqual(release_logs[0].operation_type, "release")

    def test_metrics_consistency(self):
        """Prueba consistencia entre logs y métricas."""
        # Realizar operaciones
        reserve_activity(self.activity_availability.id, 2)
        release_activity(self.activity_availability.id, 1)
        
        # Actualizar métricas
        metrics = StockAuditService.update_stock_metrics(
            product_type="activity",
            product_id=self.activity_availability.id,
            total_capacity=20,
            current_reserved=6,  # 5 originales + 2 - 1
            current_available=14,
            as_of_date=timezone.now().date()
        )
        
        # Verificar que los contadores coinciden con los logs
        reserve_logs = StockAuditLog.objects.filter(
            product_type="activity",
            product_id=self.activity_availability.id,
            operation_type="reserve",
            success=True
        ).count()
        
        release_logs = StockAuditLog.objects.filter(
            product_type="activity",
            product_id=self.activity_availability.id,
            operation_type="release",
            success=True
        ).count()
        
        self.assertEqual(metrics.total_reservations, reserve_logs)
        self.assertEqual(metrics.total_releases, release_logs)

    def test_audit_system_performance(self):
        """Prueba rendimiento básico del sistema de auditoría."""
        import time
        
        # Medir tiempo de creación de logs
        start_time = time.time()
        
        for i in range(10):
            StockAuditService.log_stock_operation(
                operation_type="reserve",
                product_type="activity",
                product_id=self.activity_availability.id,
                quantity=1,
                success=True
            )
        
        end_time = time.time()
        
        # Debería completarse en menos de 1 segundo
        self.assertLess(end_time - start_time, 1.0)
        
        # Medir tiempo de consulta
        start_time = time.time()
        logs = StockAuditQueryService.get_audit_logs(
            product_type="activity",
            limit=50
        )
        end_time = time.time()
        
        # La consulta debería completarse en menos de 1 segundo
        self.assertLess(end_time - start_time, 1.0)
        self.assertGreater(len(logs), 0)

    def test_all_product_types_audit_support(self):
        """Prueba que todos los tipos de productos soporten auditoría."""
        # Crear datos de prueba para todos los tipos de productos
        from api.products.models import Transportation, TransportationAvailability, Room, RoomAvailability, Flights
        
        # Crear transporte
        transportation = Transportation.objects.create(
            origin=self.location,
            destination=self.location,
            type="bus",
            description="Test transportation",
            capacity=30
        )
        
        # Crear disponibilidad de transporte
        transportation_availability = TransportationAvailability.objects.create(
            transportation=transportation,
            departure_date=date.today() + timedelta(days=1),
            departure_time=time(10, 0),
            arrival_date=date.today() + timedelta(days=1),
            arrival_time=time(12, 0),
            total_seats=30,
            reserved_seats=10,
            price=Decimal("50.00"),
            currency="USD"
        )
        
        # Crear habitación
        room = Room.objects.create(
            lodgment=self.lodgment,
            room_type="double",
            name="Test Room",
            capacity=2,
            base_price_per_night=Decimal("100.00"),
            currency="USD"
        )
        
        # Crear disponibilidad de habitación
        room_availability = RoomAvailability.objects.create(
            room=room,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            available_quantity=5,
            max_quantity=5,
            currency="USD"
        )
        
        # Crear vuelo
        flight = Flights.objects.create(
            airline="Test Airline",
            flight_number="TA123",
            origin=self.location,
            destination=self.location,
            departure_date=date.today() + timedelta(days=1),
            arrival_date=date.today() + timedelta(days=1),
            duration_hours=2,
            departure_time=time(10, 0),
            arrival_time=time(12, 0),
            class_flight="Economy",
            available_seats=50,
            capacity=50,
            luggage_info="20kg",
            aircraft_type="Boeing 737"
        )
        
        # Probar auditoría para cada tipo de producto
        product_types = [
            ("activity", self.activity_availability.id),
            ("transportation", transportation_availability.id),
            ("room", room_availability.id),
            ("flight", flight.id)
        ]
        
        for product_type, product_id in product_types:
            # Crear log de auditoría
            log = StockAuditService.log_stock_operation(
                operation_type="reserve",
                product_type=product_type,
                product_id=product_id,
                quantity=2,
                success=True
            )
            
            # Verificar que se creó correctamente
            self.assertIsNotNone(log)
            self.assertEqual(log.product_type, product_type)
            self.assertEqual(log.product_id, product_id)
            self.assertEqual(log.operation_type, "reserve")
            self.assertEqual(log.quantity, 2)
            self.assertTrue(log.success)
            
            # Verificar que se puede consultar
            logs = StockAuditQueryService.get_audit_logs(
                product_type=product_type,
                product_id=product_id
            )
            self.assertGreater(len(logs), 0)
            self.assertEqual(logs[0].product_type, product_type)

    def test_transportation_audit_logging(self):
        """Prueba logging específico de operaciones de transporte."""
        from api.products.models import Transportation, TransportationAvailability
        
        # Crear transporte
        transportation = Transportation.objects.create(
            origin=self.location,
            destination=self.location,
            type="bus",
            description="Test transportation",
            capacity=30
        )
        
        # Crear disponibilidad de transporte
        transportation_availability = TransportationAvailability.objects.create(
            transportation=transportation,
            departure_date=date.today() + timedelta(days=1),
            departure_time=time(10, 0),
            arrival_date=date.today() + timedelta(days=1),
            arrival_time=time(12, 0),
            total_seats=30,
            reserved_seats=10,
            price=Decimal("50.00"),
            currency="USD"
        )
        
        # Probar logging específico de transporte
        log = StockAuditService.log_transportation_stock_operation(
            operation_type="reserve",
            availability_id=transportation_availability.id,
            quantity=5,
            previous_reserved=10,
            new_reserved=15,
            success=True
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.product_type, "transportation")
        self.assertEqual(log.product_id, transportation_availability.id)
        self.assertEqual(log.operation_type, "reserve")
        self.assertEqual(log.quantity, 5)
        self.assertEqual(log.previous_stock, 10)
        self.assertEqual(log.new_stock, 15)
        self.assertTrue(log.success)

    def test_room_audit_logging(self):
        """Prueba logging específico de operaciones de habitaciones."""
        from api.products.models import Room, RoomAvailability
        
        # Crear habitación
        room = Room.objects.create(
            lodgment=self.lodgment,
            room_type="double",
            name="Test Room",
            capacity=2,
            base_price_per_night=Decimal("100.00"),
            currency="USD"
        )
        
        # Crear disponibilidad de habitación
        room_availability = RoomAvailability.objects.create(
            room=room,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            available_quantity=5,
            max_quantity=5,
            currency="USD"
        )
        
        # Probar logging específico de habitaciones
        log = StockAuditService.log_room_stock_operation(
            operation_type="reserve",
            availability_id=room_availability.id,
            quantity=2,
            previous_available=5,
            new_available=3,
            success=True
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.product_type, "room")
        self.assertEqual(log.product_id, room_availability.id)
        self.assertEqual(log.operation_type, "reserve")
        self.assertEqual(log.quantity, 2)
        self.assertEqual(log.previous_stock, 5)
        self.assertEqual(log.new_stock, 3)
        self.assertTrue(log.success)

    def test_flight_audit_logging(self):
        """Prueba logging específico de operaciones de vuelos."""
        from api.products.models import Flights
        
        # Crear vuelo
        flight = Flights.objects.create(
            airline="Test Airline",
            flight_number="TA123",
            origin=self.location,
            destination=self.location,
            departure_date=date.today() + timedelta(days=1),
            arrival_date=date.today() + timedelta(days=1),
            duration_hours=2,
            departure_time=time(10, 0),
            arrival_time=time(12, 0),
            class_flight="Economy",
            available_seats=50,
            capacity=50,
            luggage_info="20kg",
            aircraft_type="Boeing 737"
        )
        
        # Probar logging específico de vuelos
        log = StockAuditService.log_flight_stock_operation(
            operation_type="reserve",
            flight_id=flight.id,
            quantity=3,
            previous_available=50,
            new_available=47,
            success=True
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.product_type, "flight")
        self.assertEqual(log.product_id, flight.id)
        self.assertEqual(log.operation_type, "reserve")
        self.assertEqual(log.quantity, 3)
        self.assertEqual(log.previous_stock, 50)
        self.assertEqual(log.new_stock, 47)
        self.assertTrue(log.success)

    def test_audit_system_coverage(self):
        """Prueba cobertura completa del sistema de auditoría."""
        # Verificar que todos los tipos de productos están soportados
        supported_types = ["activity", "transportation", "room", "flight"]
        
        for product_type in supported_types:
            # Verificar que existe el método de logging específico
            if product_type == "activity":
                method = getattr(StockAuditService, "log_activity_stock_operation", None)
            elif product_type == "transportation":
                method = getattr(StockAuditService, "log_transportation_stock_operation", None)
            elif product_type == "room":
                method = getattr(StockAuditService, "log_room_stock_operation", None)
            elif product_type == "flight":
                method = getattr(StockAuditService, "log_flight_stock_operation", None)
            
            self.assertIsNotNone(method, f"Método de logging para {product_type} no encontrado")
            
            # Verificar que el tipo está en las opciones del modelo
            self.assertIn(product_type, [choice[0] for choice in StockAuditLog.ProductType.choices]) 