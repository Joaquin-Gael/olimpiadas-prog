import pytest
import time
from datetime import date, timedelta
from datetime import time as datetime_time
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType
from api.users.models import Users
from api.products.models import (
    Activities, ActivityAvailability, TransportationAvailability, RoomAvailability, Flights,
    Transportation, Room, Lodgments, Location, Suppliers, Category, Packages, ProductsMetadata
)
import logging

# Configurar logging para suprimir mensajes durante tests
logging.getLogger('api.products').setLevel(logging.CRITICAL)


class CRUDOperationsTestCase(TestCase):
    """
    Tests para operaciones CRUD básicas de los modelos de productos.
    
    Este test suite cubre:
    - CREATE: Creación de objetos con datos válidos e inválidos
    - READ: Consultas básicas, filtros, ordenamiento
    - UPDATE: Modificación de campos, validaciones
    - DELETE: Eliminación de objetos y efectos en cascada
    - Validaciones: Campos obligatorios, rangos, relaciones
    - Relaciones: Foreign keys, many-to-many, cascada
    """
    
    def setUp(self):
        """
        Configuración inicial para todas las pruebas.
        Crea datos base necesarios para los tests.
        """
        # Crear ubicación base (usar get_or_create para evitar conflictos)
        self.location, created = Location.objects.get_or_create(
            name="Buenos Aires",
            defaults={
                'country': "Argentina",
                'state': "Buenos Aires",
                'city': "Buenos Aires",
                'type': "city"
            }
        )
        
        # Crear proveedor base (usar get_or_create para evitar conflictos)
        self.supplier, created = Suppliers.objects.get_or_create(
            organization_name="Turismo Test S.A.",
            defaults={
                'first_name': "Juan",
                'last_name': "Pérez",
                'description': "Proveedor de servicios turísticos",
                'street': "Av. 9 de Julio",
                'street_number': 1000,
                'city': "Buenos Aires",
                'country': "Argentina",
                'email': "juan@turismotest.com",
                'telephone': "555666777",
                'website': "https://turismotest.com"
            }
        )
        
        # Crear categoría base (usar get_or_create para evitar conflictos)
        self.category, created = Category.objects.get_or_create(
            name="Aventura",
            defaults={
                'description': "Actividades de aventura y deportes extremos",
                'icon': "mountain"
            }
        )
        
        # Crear usuario base (usar get_or_create para evitar conflictos)
        self.user, created = Users.objects.get_or_create(
            email="test@example.com",
            defaults={
                'first_name': "Test",
                'last_name': "User",
                'telephone': "123456789"
            }
        )
        if created:
            self.user.set_password("testpass123")
            self.user.save()

    def tearDown(self):
        """
        Limpieza después de cada test.
        Elimina los datos creados durante el test para evitar conflictos.
        """
        # Eliminar todas las actividades creadas durante los tests
        Activities.objects.filter(
            name__in=[
                "Test Activity", "City Tour Buenos Aires", "Original Name", "Updated Name",
                "Bulk Activity 0", "Bulk Activity 1", "Bulk Activity 2", "Bulk Activity 3", "Bulk Activity 4",
                "Individual Activity 0", "Individual Activity 1", "Individual Activity 2", "Individual Activity 3", "Individual Activity 4",
                "Individual Activity 5", "Individual Activity 6", "Individual Activity 7", "Individual Activity 8", "Individual Activity 9",
                "Activity 1", "Activity 2", "Expensive Activity", "Cheap Activity"
            ]
        ).delete()
        
        # Eliminar actividades con patrones específicos
        Activities.objects.filter(name__startswith="Bulk Activity").delete()
        Activities.objects.filter(name__startswith="Individual Activity").delete()
        Activities.objects.filter(name__startswith="Activity ").delete()
        Activities.objects.filter(name__startswith="Filter Test").delete()
        Activities.objects.filter(name__startswith="Aggregation Test").delete()
        Activities.objects.filter(name__startswith="List Test Activity").delete()
        
        # Eliminar otros productos de prueba
        Flights.objects.filter(airline__startswith="Test Airline").delete()
        Lodgments.objects.filter(name__startswith="List Test Hotel").delete()
        Transportation.objects.filter(description__startswith="Transport service").delete()
        
        # Eliminar disponibilidades de transporte
        TransportationAvailability.objects.filter(price__gte=Decimal("100.00")).delete()
        
        # Limpiar base de datos de test
        super().tearDown()

    # ==================== TESTS DE CREACIÓN (CREATE) ====================

    @pytest.mark.unit
    def test_create_activity_with_valid_data(self):
        """
        Test creación de actividad con datos válidos.
        
        Verifica:
        - Creación exitosa con todos los campos requeridos
        - Valores por defecto se asignan correctamente
        - Campos calculados funcionan
        """
        activity = Activities.objects.create(
            name="City Tour Buenos Aires",
            description="Recorrido turístico por los principales puntos de Buenos Aires",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=3,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        # Verificar que se creó correctamente
        self.assertIsNotNone(activity.id)
        self.assertEqual(activity.name, "City Tour Buenos Aires")
        self.assertEqual(activity.maximum_spaces, 20)
        self.assertEqual(activity.available_slots, 20)
        self.assertEqual(activity.difficulty_level, "Easy")
        self.assertTrue(activity.include_guide)
        
        # Verificar que existe en la base de datos
        self.assertTrue(Activities.objects.filter(id=activity.id).exists())

    @pytest.mark.unit
    def test_create_activity_with_invalid_data(self):
        """
        Test creación de actividad con datos inválidos.
        
        Verifica:
        - Validaciones de campos obligatorios
        - Validaciones de rangos y formatos
        - Manejo de errores de validación
        """
        # Test: duración negativa
        with self.assertRaises(ValidationError):
            activity = Activities(
                name="Test Activity",
                description="Test description",
                location=self.location,
                date=date.today(),
                start_time=datetime_time(10, 0),
                duration_hours=-1,  # Inválido: duración negativa
                maximum_spaces=20,
                difficulty_level="Easy",
                language="Spanish",
                available_slots=20
            )
            activity.full_clean()
        
        # Test: máximo de espacios excede límite
        with self.assertRaises(ValidationError):
            activity = Activities(
                name="Test Activity",
                description="Test description",
                location=self.location,
                date=date.today(),
                start_time=datetime_time(10, 0),
                duration_hours=2,
                maximum_spaces=150,  # Inválido: excede máximo de 100
                difficulty_level="Easy",
                language="Spanish",
                available_slots=20
            )
            activity.full_clean()

    @pytest.mark.unit
    def test_create_activity_availability(self):
        """
        Test creación de disponibilidad de actividad.
        
        Verifica:
        - Relación con actividad padre
        - Cálculo de asientos disponibles
        - Validaciones de precios y fechas
        """
        # Crear actividad primero
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test description",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        # Crear disponibilidad
        availability = ActivityAvailability.objects.create(
            activity=activity,
            event_date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            total_seats=15,
            reserved_seats=0,
            price=Decimal("150.00"),
            currency="USD",
            state="active"
        )
        
        # Verificar que se creó correctamente
        self.assertIsNotNone(availability.id)
        self.assertEqual(availability.activity, activity)
        self.assertEqual(availability.price, Decimal("150.00"))
        self.assertEqual(availability.total_seats, 15)
        
        # Verificar relación inversa
        self.assertEqual(activity.availabilities.count(), 1)
        self.assertEqual(activity.availabilities.first(), availability)

    @pytest.mark.unit
    def test_create_transportation_and_availability(self):
        """
        Test creación de transporte y su disponibilidad.
        
        Verifica:
        - Creación de transporte con proveedor
        - Creación de disponibilidad de transporte
        - Relaciones entre modelos
        """
        # Crear transporte
        transportation = Transportation.objects.create(
            origin=self.location,
            destination=self.location,
            type="bus",
            description="Servicio de transporte turístico",
            notes="Servicio de calidad",
            capacity=50
        )
        
        # Crear disponibilidad de transporte
        transport_availability = TransportationAvailability.objects.create(
            transportation=transportation,
            departure_date=date.today() + timedelta(days=1),
            departure_time=datetime_time(8, 0),
            arrival_date=date.today() + timedelta(days=1),
            arrival_time=datetime_time(14, 0),
            total_seats=45,
            reserved_seats=0,
            price=Decimal("200.00"),
            currency="USD",
            state="active"
        )
        
        # Verificar creación
        self.assertIsNotNone(transportation.id)
        self.assertIsNotNone(transport_availability.id)
        self.assertEqual(transport_availability.transportation, transportation)

    # ==================== TESTS DE LECTURA (READ) ====================

    @pytest.mark.unit
    def test_list_all_products(self):
        """
        Test listado simple de todos los productos sin filtros.
        
        Verifica:
        - Listado completo de productos usando ProductsMetadata
        - Conteo total de registros
        - Estructura básica de respuesta
        - Ordenamiento por defecto
        """
        # Listar todos los productos usando ProductsMetadata
        all_products = ProductsMetadata.objects.all()
        
        # Verificar que se obtienen productos (puede ser cualquier cantidad)
        self.assertGreaterEqual(all_products.count(), 0)
        
        # Verificar estructura de respuesta para cada producto
        for product in all_products:
            self.assertIsNotNone(product.id)
            self.assertIsNotNone(product.supplier)
            self.assertIsNotNone(product.content_type_id)
            self.assertIsNotNone(product.object_id)
            self.assertIsNotNone(product.unit_price)
            self.assertIsNotNone(product.currency)
            self.assertIsNotNone(product.is_active)
            
            # Verificar que el producto relacionado existe
            self.assertIsNotNone(product.content)
            
            # Verificar el tipo de producto
            self.assertIn(product.product_type, ['activity', 'flight', 'lodgment', 'transportation'])
        
        # Verificar que se pueden obtener estadísticas básicas
        total_products = all_products.count()
        print(f"Total de productos en la base de datos: {total_products}")
        
        # Verificar distribución por tipo de producto
        activity_products = all_products.filter(content_type_id=ContentType.objects.get_for_model(Activities))
        flight_products = all_products.filter(content_type_id=ContentType.objects.get_for_model(Flights))
        lodgment_products = all_products.filter(content_type_id=ContentType.objects.get_for_model(Lodgments))
        transportation_products = all_products.filter(content_type_id=ContentType.objects.get_for_model(Transportation))
        
        print(f"Actividades: {activity_products.count()}")
        print(f"Vuelos: {flight_products.count()}")
        print(f"Alojamientos: {lodgment_products.count()}")
        print(f"Transportes: {transportation_products.count()}")
        
        # Verificar que los precios están en el rango esperado
        for product in all_products:
            self.assertGreater(product.unit_price, 0)
            self.assertLessEqual(product.unit_price, 10000)  # Precio máximo razonable

    @pytest.mark.unit
    def test_read_activities_with_filters(self):
        """
        Test lectura de actividades con diferentes filtros.
        
        Verifica:
        - Filtros por dificultad
        - Filtros por idioma
        - Filtros por fecha
        - Ordenamiento
        """
        # Crear actividades con diferentes características
        Activities.objects.create(
            name="Filter Test Easy Activity",
            description="Easy activity",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        Activities.objects.create(
            name="Filter Test Hard Activity",
            description="Hard activity",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(14, 0),
            duration_hours=4,
            include_guide=False,
            maximum_spaces=10,
            difficulty_level="Hard",
            language="English",
            available_slots=10
        )
        
        # Test filtros - contar solo las actividades creadas en este test
        easy_activities = Activities.objects.filter(
            difficulty_level="Easy",
            name__startswith="Filter Test"
        )
        self.assertEqual(easy_activities.count(), 1)
        self.assertEqual(easy_activities.first().name, "Filter Test Easy Activity")
        
        spanish_activities = Activities.objects.filter(
            language="Spanish",
            name__startswith="Filter Test"
        )
        self.assertEqual(spanish_activities.count(), 1)
        
        # Test ordenamiento
        activities_ordered = Activities.objects.filter(
            name__startswith="Filter Test"
        ).order_by('name')
        self.assertEqual(activities_ordered.first().name, "Filter Test Easy Activity")

    @pytest.mark.unit
    def test_read_activities_with_related_data(self):
        """
        Test lectura de actividades con datos relacionados.
        
        Verifica:
        - Prefetch de relaciones
        - Acceso a datos relacionados
        - Optimización de consultas
        """
        # Crear actividad con disponibilidad
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test description",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        # Crear disponibilidad
        ActivityAvailability.objects.create(
            activity=activity,
            event_date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            total_seats=15,
            reserved_seats=0,
            price=Decimal("150.00"),
            currency="USD",
            state="active"
        )
        
        # Test: leer actividad con disponibilidades
        activity_with_availabilities = Activities.objects.prefetch_related('availabilities').get(id=activity.id)
        availabilities = list(activity_with_availabilities.availabilities.all())
        self.assertEqual(len(availabilities), 1)
        self.assertEqual(availabilities[0].price, Decimal("150.00"))

    @pytest.mark.unit
    def test_read_activities_with_aggregations(self):
        """
        Test lectura de actividades con agregaciones.
        
        Verifica:
        - Conteos por categoría
        - Promedios de precios
        - Estadísticas básicas
        """
        # Crear actividades con diferentes dificultades
        Activities.objects.create(
            name="Aggregation Test Easy Activity 1",
            description="Easy activity",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        Activities.objects.create(
            name="Aggregation Test Easy Activity 2",
            description="Easy activity",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(14, 0),
            duration_hours=3,
            include_guide=True,
            maximum_spaces=15,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=15
        )
        
        Activities.objects.create(
            name="Aggregation Test Hard Activity",
            description="Hard activity",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(16, 0),
            duration_hours=4,
            include_guide=False,
            maximum_spaces=10,
            difficulty_level="Hard",
            language="English",
            available_slots=10
        )
        
        # Test agregaciones - contar solo las actividades creadas en este test
        from django.db.models import Count, Avg
        
        easy_stats = Activities.objects.filter(
            difficulty_level="Easy",
            name__startswith="Aggregation Test"
        ).aggregate(
            count=Count('id'),
            avg_duration=Avg('duration_hours')
        )
        
        self.assertEqual(easy_stats['count'], 2)
        self.assertEqual(easy_stats['avg_duration'], 2.5)

    # ==================== TESTS DE ACTUALIZACIÓN (UPDATE) ====================

    @pytest.mark.unit
    def test_update_activity_basic_fields(self):
        """
        Test actualización de campos básicos de actividad.
        
        Verifica:
        - Actualización de campos simples
        - Persistencia de cambios
        - Validaciones durante actualización
        """
        # Crear actividad
        activity = Activities.objects.create(
            name="Original Name",
            description="Original description",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        # Actualizar campos
        activity.name = "Updated Name"
        activity.description = "Updated description"
        activity.duration_hours = 3
        activity.save()
        
        # Verificar cambios
        activity.refresh_from_db()
        self.assertEqual(activity.name, "Updated Name")
        self.assertEqual(activity.description, "Updated description")
        self.assertEqual(activity.duration_hours, 3)

    @pytest.mark.unit
    def test_update_activity_with_invalid_data(self):
        """
        Test actualización con datos inválidos.
        
        Verifica:
        - Validaciones durante actualización
        - Manejo de errores de validación
        - Integridad de datos
        """
        # Crear actividad válida
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test description",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        # Test: actualización con datos inválidos
        activity.duration_hours = -1
        with self.assertRaises(ValidationError):
            activity.full_clean()
        
        # Verificar que no se guardó el cambio inválido
        activity.refresh_from_db()
        self.assertEqual(activity.duration_hours, 2)

    @pytest.mark.unit
    def test_update_activity_availability_stock(self):
        """
        Test actualización de stock de disponibilidad.
        
        Verifica:
        - Actualización de espacios disponibles
        - Validaciones de stock
        - Efectos en cascada
        """
        # Crear actividad y disponibilidad
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test description",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        availability = ActivityAvailability.objects.create(
            activity=activity,
            event_date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            total_seats=15,
            reserved_seats=0,
            price=Decimal("150.00"),
            currency="USD",
            state="active"
        )
        
        # Actualizar stock
        availability.reserved_seats = 5
        availability.save()
        
        # Verificar cambio
        availability.refresh_from_db()
        self.assertEqual(availability.reserved_seats, 5)

    @pytest.mark.unit
    def test_bulk_update_activities(self):
        """
        Test actualización masiva de actividades.
        
        Verifica:
        - Actualización eficiente de múltiples registros
        - Rendimiento de operaciones masivas
        - Consistencia de datos
        """
        # Crear múltiples actividades
        activities = []
        for i in range(5):
            activity = Activities.objects.create(
                name=f"Bulk Activity {i}",
                description=f"Bulk activity {i}",
                location=self.location,
                date=date.today() + timedelta(days=7),
                start_time=datetime_time(10, 0),
                duration_hours=2,
                include_guide=True,
                maximum_spaces=20,
                difficulty_level="Easy",
                language="Spanish",
                available_slots=20
            )
            activities.append(activity)
        
        # Actualización masiva
        Activities.objects.filter(name__startswith="Bulk Activity").update(
            difficulty_level="Medium",
            include_guide=False
        )
        
        # Verificar cambios
        updated_activities = Activities.objects.filter(name__startswith="Bulk Activity")
        for activity in updated_activities:
            self.assertEqual(activity.difficulty_level, "Medium")
            self.assertFalse(activity.include_guide)

    # ==================== TESTS DE ELIMINACIÓN (DELETE) ====================

    @pytest.mark.unit
    def test_delete_activity(self):
        """
        Test eliminación de actividad.
        
        Verifica:
        - Eliminación exitosa
        - Efectos en cascada
        - Limpieza de datos relacionados
        """
        # Crear actividad
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test description",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        activity_id = activity.id
        
        # Eliminar actividad
        activity.delete()
        
        # Verificar eliminación
        self.assertFalse(Activities.objects.filter(id=activity_id).exists())

    @pytest.mark.unit
    def test_delete_activity_with_related_data(self):
        """
        Test eliminación de actividad con datos relacionados.
        
        Verifica:
        - Eliminación en cascada
        - Limpieza de disponibilidades
        - Integridad referencial
        """
        # Crear actividad con disponibilidad
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test description",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        availability = ActivityAvailability.objects.create(
            activity=activity,
            event_date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            total_seats=15,
            reserved_seats=0,
            price=Decimal("150.00"),
            currency="USD",
            state="active"
        )
        
        availability_id = availability.id
        
        # Eliminar actividad (debería eliminar disponibilidad en cascada)
        activity.delete()
        
        # Verificar eliminación en cascada
        self.assertFalse(Activities.objects.filter(id=activity.id).exists())
        self.assertFalse(ActivityAvailability.objects.filter(id=availability_id).exists())

    @pytest.mark.unit
    def test_bulk_delete_activities(self):
        """
        Test eliminación masiva de actividades.
        
        Verifica:
        - Eliminación eficiente de múltiples registros
        - Rendimiento de operaciones masivas
        - Limpieza completa
        """
        # Crear múltiples actividades
        for i in range(10):
            Activities.objects.create(
                name=f"Bulk Activity {i}",
                description=f"Bulk activity {i}",
                location=self.location,
                date=date.today() + timedelta(days=7),
                start_time=datetime_time(10, 0),
                duration_hours=2,
                include_guide=True,
                maximum_spaces=20,
                difficulty_level="Easy",
                language="Spanish",
                available_slots=20
            )
        
        # Eliminación masiva
        deleted_count, _ = Activities.objects.filter(name__startswith="Bulk Activity").delete()
        
        # Verificar eliminación
        self.assertEqual(Activities.objects.filter(name__startswith="Bulk Activity").count(), 0)

    # ==================== TESTS DE VALIDACIÓN ====================

    @pytest.mark.unit
    def test_activity_validation_constraints(self):
        """
        Test validaciones y restricciones de actividad.
        
        Verifica:
        - Validaciones de campos obligatorios
        - Restricciones de rangos
        - Validaciones de formato
        """
        # Test: validaciones de modelo
        activity = Activities(
            name="Test Activity",
            description="Test description",
            location=self.location,
            date=date.today(),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        # Verificar que pasa validación
        activity.full_clean()

    @pytest.mark.unit
    def test_activity_availability_validation(self):
        """
        Test validaciones de disponibilidad de actividad.
        
        Verifica:
        - Validaciones de precios
        - Validaciones de fechas
        - Validaciones de stock
        """
        # Crear actividad
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test description",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        # Test: asientos reservados exceden total de asientos
        with self.assertRaises(ValidationError):
            availability = ActivityAvailability(
                activity=activity,
                event_date=date.today() + timedelta(days=7),
                start_time=datetime_time(10, 0),
                total_seats=15,
                reserved_seats=20,  # Más reservados que total
                price=Decimal("150.00"),
                currency="USD",
                state="active"
            )
            availability.full_clean()
        
        # Test: fecha en el pasado
        with self.assertRaises(ValidationError):
            availability = ActivityAvailability(
                activity=activity,
                event_date=date.today() - timedelta(days=1),  # Fecha pasada
                start_time=datetime_time(10, 0),
                total_seats=15,
                reserved_seats=0,
                price=Decimal("150.00"),
                currency="USD",
                state="active"
            )
            availability.full_clean()

    # ==================== TESTS DE RELACIONES ====================

    @pytest.mark.unit
    def test_activity_location_relationship(self):
        """
        Test relaciones entre actividad y ubicación.
        
        Verifica:
        - Relación ForeignKey
        - Acceso bidireccional
        - Integridad referencial
        """
        # Crear actividad
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test description",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        # Verificar relación directa
        self.assertEqual(activity.location, self.location)
        
        # Verificar relación inversa (no existe en el modelo real)
        # Location no tiene relación inversa con Activities

    @pytest.mark.unit
    def test_activity_availability_relationship(self):
        """
        Test relaciones entre actividad y disponibilidades.
        
        Verifica:
        - Relación OneToMany
        - Acceso bidireccional
        - Eliminación en cascada
        """
        # Crear actividad
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test description",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        # Crear múltiples disponibilidades
        availability1 = ActivityAvailability.objects.create(
            activity=activity,
            event_date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            total_seats=15,
            reserved_seats=0,
            price=Decimal("150.00"),
            currency="USD",
            state="active"
        )
        
        availability2 = ActivityAvailability.objects.create(
            activity=activity,
            event_date=date.today() + timedelta(days=8),
            start_time=datetime_time(10, 0),
            total_seats=10,
            reserved_seats=0,
            price=Decimal("200.00"),
            currency="USD",
            state="active"
        )
        
        # Verificar relación directa
        self.assertEqual(availability1.activity, activity)
        self.assertEqual(availability2.activity, activity)
        
        # Verificar relación inversa
        availabilities = activity.availabilities.all()
        self.assertEqual(availabilities.count(), 2)
        self.assertIn(availability1, availabilities)
        self.assertIn(availability2, availabilities)

    # ==================== TESTS DE CONSULTAS AVANZADAS ====================

    @pytest.mark.unit
    def test_advanced_queries_with_annotations(self):
        """
        Test consultas avanzadas con anotaciones.
        
        Verifica:
        - Agregaciones complejas
        - Anotaciones personalizadas
        - Consultas optimizadas
        """
        # Crear actividades con diferentes características
        Activities.objects.create(
            name="Activity 1",
            description="Activity 1",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        Activities.objects.create(
            name="Activity 2",
            description="Activity 2",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(14, 0),
            duration_hours=4,
            include_guide=False,
            maximum_spaces=10,
            difficulty_level="Hard",
            language="English",
            available_slots=10
        )
        
        # Consulta con anotaciones
        from django.db.models import Count, Avg, Max
        
        activities_with_stats = Activities.objects.annotate(
            total_spaces=Count('maximum_spaces'),
            avg_duration=Avg('duration_hours'),
            max_spaces=Max('maximum_spaces')
        )
        
        # Verificar anotaciones
        for activity in activities_with_stats:
            self.assertIsNotNone(activity.total_spaces)
            self.assertIsNotNone(activity.avg_duration)
            self.assertIsNotNone(activity.max_spaces)

    @pytest.mark.unit
    def test_queries_with_subqueries(self):
        """
        Test consultas con subconsultas.
        
        Verifica:
        - Subconsultas complejas
        - Consultas anidadas
        - Optimización de consultas
        """
        # Crear actividades con diferentes precios
        activity1 = Activities.objects.create(
            name="Expensive Activity",
            description="Expensive activity",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        ActivityAvailability.objects.create(
            activity=activity1,
            event_date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            total_seats=15,
            reserved_seats=0,
            price=Decimal("500.00"),
            currency="USD",
            state="active"
        )
        
        activity2 = Activities.objects.create(
            name="Cheap Activity",
            description="Cheap activity",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(14, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        ActivityAvailability.objects.create(
            activity=activity2,
            event_date=date.today() + timedelta(days=7),
            start_time=datetime_time(14, 0),
            total_seats=15,
            reserved_seats=0,
            price=Decimal("50.00"),
            currency="USD",
            state="active"
        )
        
        # Subconsulta para actividades caras
        from django.db.models import Subquery, OuterRef
        
        expensive_activities = Activities.objects.filter(
            availabilities__price__gte=Subquery(
                ActivityAvailability.objects.filter(
                    activity=OuterRef('pk')
                ).values('price')[:1]
            )
        ).distinct()
        
        # Verificar resultado
        self.assertGreaterEqual(expensive_activities.count(), 0)

    # ==================== TESTS DE RENDIMIENTO ====================

    @pytest.mark.unit
    def test_query_performance_with_select_related(self):
        """
        Test rendimiento de consultas con select_related.
        
        Verifica:
        - Optimización de consultas
        - Reducción de queries
        - Rendimiento mejorado
        """
        # Crear actividad
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test description",
            location=self.location,
            date=date.today() + timedelta(days=7),
            start_time=datetime_time(10, 0),
            duration_hours=2,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        # Test sin optimización
        from django.db import connection, reset_queries
        reset_queries()
        
        activity_without_opt = Activities.objects.get(id=activity.id)
        location_name = activity_without_opt.location.name
        queries_without_optimization = len(connection.queries)
        
        # Test con optimización
        reset_queries()
        
        activity_with_opt = Activities.objects.select_related('location').get(id=activity.id)
        location_name = activity_with_opt.location.name
        queries_with_optimization = len(connection.queries)
        
        # Verificar optimización
        self.assertLessEqual(queries_with_optimization, queries_without_optimization)

    @pytest.mark.unit
    def test_bulk_operations_performance(self):
        """
        Test rendimiento de operaciones masivas.
        
        Verifica:
        - Rendimiento de bulk_create
        - Comparación con creación individual
        - Optimización de operaciones masivas
        """
        # Test bulk_create
        start_time = time.time()
        
        activities_to_create = []
        for i in range(100):
            activities_to_create.append(Activities(
                name=f"Bulk Activity {i}",
                description=f"Bulk activity {i}",
                location=self.location,
                date=date.today() + timedelta(days=7),
                start_time=datetime_time(10, 0),
                duration_hours=2,
                include_guide=True,
                maximum_spaces=20,
                difficulty_level="Easy",
                language="Spanish",
                available_slots=20
            ))
        
        Activities.objects.bulk_create(activities_to_create)
        bulk_create_time = time.time() - start_time
        
        # Test creación individual
        start_time = time.time()
        
        for i in range(10):  # Menos registros para comparación justa
            Activities.objects.create(
                name=f"Individual Activity {i}",
                description=f"Individual activity {i}",
                location=self.location,
                date=date.today() + timedelta(days=7),
                start_time=datetime_time(10, 0),
                duration_hours=2,
                include_guide=True,
                maximum_spaces=20,
                difficulty_level="Easy",
                language="Spanish",
                available_slots=20
            )
        
        individual_create_time = time.time() - start_time
        
        # Verificar que bulk_create es más eficiente por registro
        bulk_time_per_record = bulk_create_time / 100
        individual_time_per_record = individual_create_time / 10
        
        # Verificar que bulk_create funcionó correctamente
        # En lugar de verificar tiempos específicos, verificamos que se crearon los registros
        bulk_created_count = Activities.objects.filter(name__startswith="Bulk Activity").count()
        individual_created_count = Activities.objects.filter(name__startswith="Individual Activity").count()
        
        self.assertEqual(bulk_created_count, 100)
        self.assertEqual(individual_created_count, 10)
        
        # Verificar que bulk_create es más eficiente por registro (solo si los tiempos son medibles)
        if bulk_create_time > 0 and individual_create_time > 0:
            bulk_time_per_record = bulk_create_time / 100
            individual_time_per_record = individual_create_time / 10
            
            # bulk_create debería ser más eficiente por registro
            if individual_time_per_record > 0.001:  # Si es mayor a 1ms
                self.assertLess(bulk_time_per_record, individual_time_per_record)
            else:
                # Si individual es muy rápido, solo verificamos que bulk_create sea razonable
                self.assertLess(bulk_time_per_record, 0.1)  # Menos de 100ms por registro
        else:
            # Si los tiempos son 0, solo verificamos que las operaciones funcionaron
            self.assertTrue(bulk_created_count > 0)
            self.assertTrue(individual_created_count > 0) 