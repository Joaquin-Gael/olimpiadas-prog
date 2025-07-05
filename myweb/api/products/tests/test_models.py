import pytest
from datetime import date, time, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from api.products.models import (
    Suppliers, Location, Activities, ActivityAvailability, Flights,
    Lodgments, Room, RoomAvailability, Transportation, TransportationAvailability,
    ProductsMetadata, Packages, ComponentPackages, Reviews, Promotions,
    Category, StockAuditLog, StockChangeHistory, StockMetrics
)


class TestSuppliers:
    """Tests para el modelo Suppliers."""
    
    @pytest.mark.unit
    def test_create_supplier_success(self, db):
        """Test crear un proveedor exitosamente."""
        supplier = Suppliers.objects.create(
            first_name="Juan",
            last_name="Pérez",
            organization_name="Turismo ABC",
            description="Agencia de viajes especializada",
            street="Av. Principal",
            street_number=123,
            city="Buenos Aires",
            country="Argentina",
            email="juan@turismo.com",
            telephone="123456789",
            website="https://turismo.com"
        )
        
        assert supplier.id is not None
        assert supplier.first_name == "Juan"
        assert supplier.last_name == "Pérez"
        assert supplier.organization_name == "Turismo ABC"
        assert supplier.email == "juan@turismo.com"
        assert supplier.is_active is True

    @pytest.mark.unit
    def test_supplier_name_property(self, db):
        """Test propiedad name del proveedor."""
        supplier = Suppliers.objects.create(
            first_name="María",
            last_name="González",
            organization_name="Viajes XYZ",
            description="Test",
            street="Test",
            street_number=123,
            city="Test",
            country="Test",
            email="test@test.com",
            telephone="123456789",
            website="https://test.com"
        )
        
        assert supplier.name == "María González"

    @pytest.mark.unit
    def test_supplier_street_number_validation(self, db):
        """Test validación del número de calle."""
        # Número válido
        supplier = Suppliers.objects.create(
            first_name="Test",
            last_name="Test",
            organization_name="Test",
            description="Test",
            street="Test",
            street_number=100,
            city="Test",
            country="Test",
            email="test@test.com",
            telephone="123456789",
            website="https://test.com"
        )
        assert supplier.street_number == 100
        
        # Número inválido (debería fallar)
        with pytest.raises(ValidationError):
            Suppliers.objects.create(
                first_name="Test",
                last_name="Test",
                organization_name="Test",
                description="Test",
                street="Test",
                street_number=300000,  # Inválido (máximo 200,000)
                city="Test",
                country="Test",
                email="test@test.com",
                telephone="123456789",
                website="https://test.com"
            )


class TestLocation:
    """Tests para el modelo Location."""
    
    @pytest.mark.unit
    def test_create_location_success(self, db):
        """Test crear una ubicación exitosamente."""
        location = Location.objects.create(
            name="Buenos Aires",
            country="Argentina",
            state="Buenos Aires",
            city="Buenos Aires",
            type="city",
            latitude=Decimal("-34.6118"),
            longitude=Decimal("-58.3960")
        )
        
        assert location.id is not None
        assert location.name == "Buenos Aires"
        assert location.country == "Argentina"
        assert location.type == "city"
        assert location.is_active is True

    @pytest.mark.unit
    def test_location_hierarchy(self, db):
        """Test jerarquía de ubicaciones."""
        # Crear país
        country = Location.objects.create(
            name="Argentina",
            country="Argentina",
            type="country"
        )
        
        # Crear ciudad que pertenece al país
        city = Location.objects.create(
            name="Buenos Aires",
            country="Argentina",
            state="Buenos Aires",
            city="Buenos Aires",
            type="city",
            parent=countrye
        )
        
        assert city.parent == country
        assert country.children.first() == city

    @pytest.mark.unit
    def test_location_str_representation(self, db):
        """Test representación string de ubicación."""
        location = Location.objects.create(
            name="Buenos Aires",
            country="Argentina",
            state="Buenos Aires",
            city="Buenos Aires",
            type="city"
        )
        
        assert str(location) == "Buenos Aires, Buenos Aires, Argentina"


class TestActivities:
    """Tests para el modelo Activities."""
    
    @pytest.mark.unit
    def test_create_activity_success(self, db):
        """Test crear una actividad exitosamente."""
        location = Location.objects.create(
            name="Buenos Aires",
            country="Argentina",
            state="Buenos Aires",
            city="Buenos Aires",
            type="city"
        )
        
        activity = Activities.objects.create(
            name="City Tour",
            description="Recorrido por los principales puntos de la ciudad",
            location=location,
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            duration_hours=3,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        assert activity.id is not None
        assert activity.name == "City Tour"
        assert activity.location == location
        assert activity.duration_hours == 3
        assert activity.include_guide is True
        assert activity.is_active is True

    @pytest.mark.unit
    def test_activity_duration_validation(self, db):
        """Test validación de duración de actividad."""
        location = Location.objects.create(
            name="Test",
            country="Test",
            type="city"
        )
        
        # Duración válida
        activity = Activities.objects.create(
            name="Test",
            description="Test",
            location=location,
            date=date.today(),
            start_time=time(10, 0),
            duration_hours=12,  # Válido
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        assert activity.duration_hours == 12
        
        # Duración inválida (debería fallar)
        with pytest.raises(ValidationError):
            Activities.objects.create(
                name="Test",
                description="Test",
                location=location,
                date=date.today(),
                start_time=time(10, 0),
                duration_hours=25,  # Inválido (máximo 24)
                include_guide=True,
                maximum_spaces=20,
                difficulty_level="Easy",
                language="Spanish",
                available_slots=20
            )

    @pytest.mark.unit
    def test_activity_location_relationship(self, db):
        """Test relación entre actividad y ubicación."""
        location = Location.objects.create(
            name="Buenos Aires",
            country="Argentina",
            type="city"
        )
        
        activity = Activities.objects.create(
            name="City Tour",
            description="Test",
            location=location,
            date=date.today(),
            start_time=time(10, 0),
            duration_hours=3,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        assert activity.location == location
        # Verificar relación inversa
        assert location.activities_set.first() == activity


class TestActivityAvailability:
    """Tests para el modelo ActivityAvailability."""
    
    @pytest.mark.unit
    def test_create_activity_availability_success(self, db):
        """Test crear disponibilidad de actividad exitosamente."""
        location = Location.objects.create(
            name="Test",
            country="Test",
            type="city"
        )
        
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test",
            location=location,
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            duration_hours=3,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        availability = ActivityAvailability.objects.create(
            activity=activity,
            event_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            total_seats=20,
            reserved_seats=5,
            price=Decimal("100.00"),
            currency="USD",
            state="active"
        )
        
        assert availability.id is not None
        assert availability.activity == activity
        assert availability.total_seats == 20
        assert availability.reserved_seats == 5
        assert availability.price == Decimal("100.00")
        assert availability.state == "active"

    @pytest.mark.unit
    def test_activity_availability_validation(self, db):
        """Test validaciones de disponibilidad de actividad."""
        location = Location.objects.create(
            name="Test",
            country="Test",
            type="city"
        )
        
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test",
            location=location,
            date=date.today(),
            start_time=time(10, 0),
            duration_hours=3,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        # Reservas mayores que total (debería fallar)
        with pytest.raises(ValidationError):
            availability = ActivityAvailability(
                activity=activity,
                event_date=date.today(),
                start_time=time(10, 0),
                total_seats=10,
                reserved_seats=15,  # Mayor que total_seats
                price=Decimal("100.00"),
                currency="USD",
                state="active"
            )
            availability.full_clean()


class TestFlights:
    """Tests para el modelo Flights."""
    
    @pytest.mark.unit
    def test_create_flight_success(self, db):
        """Test crear un vuelo exitosamente."""
        location = Location.objects.create(
            name="Buenos Aires",
            country="Argentina",
            type="city"
        )
        
        flight = Flights.objects.create(
            airline="Aerolíneas Argentinas",
            flight_number="AR1234",
            origin=location,
            destination=location,
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
        
        assert flight.id is not None
        assert flight.airline == "Aerolíneas Argentinas"
        assert flight.flight_number == "AR1234"
        assert flight.origin == location
        assert flight.destination == location
        assert flight.class_flight == "Economy"
        assert flight.is_active is True

    @pytest.mark.unit
    def test_flight_capacity_validation(self, db):
        """Test validación de capacidad de vuelo."""
        location = Location.objects.create(
            name="Test",
            country="Test",
            type="city"
        )
        
        # Capacidad válida
        flight = Flights.objects.create(
            airline="Test",
            flight_number="TEST123",
            origin=location,
            destination=location,
            departure_date=date.today(),
            arrival_date=date.today(),
            duration_hours=2,
            departure_time=time(14, 0),
            arrival_time=time(16, 0),
            class_flight="Economy",
            available_seats=100,
            capacity=100,
            luggage_info="Test",
            aircraft_type="Test"
        )
        assert flight.capacity == 100
        
        # Capacidad inválida (debería fallar)
        with pytest.raises(ValidationError):
            Flights.objects.create(
                airline="Test",
                flight_number="TEST456",
                origin=location,
                destination=location,
                departure_date=date.today(),
                arrival_date=date.today(),
                duration_hours=2,
                departure_time=time(14, 0),
                arrival_time=time(16, 0),
                class_flight="Economy",
                available_seats=600,
                capacity=600,  # Inválido (máximo 500)
                luggage_info="Test",
                aircraft_type="Test"
            )


class TestLodgments:
    """Tests para el modelo Lodgments."""
    
    @pytest.mark.unit
    def test_create_lodgment_success(self, db):
        """Test crear un alojamiento exitosamente."""
        location = Location.objects.create(
            name="Buenos Aires",
            country="Argentina",
            type="city"
        )
        
        lodgment = Lodgments.objects.create(
            name="Hotel Plaza",
            description="Hotel de lujo en el centro",
            location=location,
            type="hotel",
            max_guests=10,
            contact_phone="123456789",
            contact_email="info@hotelplaza.com",
            amenities=["wifi", "pool", "gym"],
            date_checkin=date.today() + timedelta(days=3),
            date_checkout=date.today() + timedelta(days=5)
        )
        
        assert lodgment.id is not None
        assert lodgment.name == "Hotel Plaza"
        assert lodgment.location == location
        assert lodgment.type == "hotel"
        assert lodgment.max_guests == 10
        assert lodgment.amenities == ["wifi", "pool", "gym"]
        assert lodgment.is_active is True

    @pytest.mark.unit
    def test_lodgment_is_available_property(self, db):
        """Test propiedad is_available del alojamiento."""
        location = Location.objects.create(
            name="Test",
            country="Test",
            type="city"
        )
        
        # Alojamiento disponible
        lodgment = Lodgments.objects.create(
            name="Test Hotel",
            description="Test",
            location=location,
            type="hotel",
            max_guests=5,
            date_checkin=date.today() + timedelta(days=1),
            date_checkout=date.today() + timedelta(days=3)
        )
        
        assert lodgment.is_available is True
        
        # Alojamiento no disponible (fecha pasada)
        lodgment_past = Lodgments.objects.create(
            name="Test Hotel Past",
            description="Test",
            location=location,
            type="hotel",
            max_guests=5,
            date_checkin=date.today() - timedelta(days=3),
            date_checkout=date.today() - timedelta(days=1)
        )
        
        assert lodgment_past.is_available is False


class TestRoom:
    """Tests para el modelo Room."""
    
    @pytest.mark.unit
    def test_create_room_success(self, db):
        """Test crear una habitación exitosamente."""
        location = Location.objects.create(
            name="Test",
            country="Test",
            type="city"
        )
        
        lodgment = Lodgments.objects.create(
            name="Test Hotel",
            description="Test",
            location=location,
            type="hotel",
            max_guests=5,
            date_checkin=date.today(),
            date_checkout=date.today() + timedelta(days=2)
        )
        
        room = Room.objects.create(
            lodgment=lodgment,
            room_type="double",
            name="Habitación 101",
            description="Habitación doble con vista",
            capacity=2,
            has_private_bathroom=True,
            has_balcony=True,
            has_air_conditioning=True,
            has_wifi=True,
            base_price_per_night=Decimal("80.00"),
            currency="USD"
        )
        
        assert room.id is not None
        assert room.lodgment == lodgment
        assert room.room_type == "double"
        assert room.name == "Habitación 101"
        assert room.capacity == 2
        assert room.has_private_bathroom is True
        assert room.base_price_per_night == Decimal("80.00")
        assert room.is_active is True

    @pytest.mark.unit
    def test_room_capacity_validation(self, db):
        """Test validación de capacidad de habitación."""
        location = Location.objects.create(
            name="Test",
            country="Test",
            type="city"
        )
        
        lodgment = Lodgments.objects.create(
            name="Test Hotel",
            description="Test",
            location=location,
            type="hotel",
            max_guests=5,
            date_checkin=date.today(),
            date_checkout=date.today() + timedelta(days=2)
        )
        
        # Capacidad válida
        room = Room.objects.create(
            lodgment=lodgment,
            room_type="single",
            name="Test Room",
            capacity=1,
            base_price_per_night=Decimal("50.00"),
            currency="USD"
        )
        assert room.capacity == 1
        
        # Capacidad inválida (debería fallar)
        with pytest.raises(ValidationError):
            Room.objects.create(
                lodgment=lodgment,
                room_type="test",
                name="Test Room Invalid",
                capacity=25,  # Inválido (máximo 20)
                base_price_per_night=Decimal("50.00"),
                currency="USD"
            )


class TestTransportation:
    """Tests para el modelo Transportation."""
    
    @pytest.mark.unit
    def test_create_transportation_success(self, db):
        """Test crear transporte exitosamente."""
        location = Location.objects.create(
            name="Buenos Aires",
            country="Argentina",
            type="city"
        )
        
        transportation = Transportation.objects.create(
            origin=location,
            destination=location,
            type="bus",
            description="Servicio de bus interurbano",
            notes="Incluye wifi y aire acondicionado",
            capacity=30
        )
        
        assert transportation.id is not None
        assert transportation.origin == location
        assert transportation.destination == location
        assert transportation.type == "bus"
        assert transportation.capacity == 30
        assert transportation.is_active is True

    @pytest.mark.unit
    def test_transportation_is_available_property(self, db):
        """Test propiedad is_available del transporte."""
        location = Location.objects.create(
            name="Test",
            country="Test",
            type="city"
        )
        
        transportation = Transportation.objects.create(
            origin=location,
            destination=location,
            type="bus",
            description="Test",
            capacity=30
        )
        
        assert transportation.is_available is True
        
        # Desactivar transporte
        transportation.is_active = False
        transportation.save()
        
        assert transportation.is_available is False


class TestProductsMetadata:
    """Tests para el modelo ProductsMetadata."""
    
    @pytest.mark.unit
    def test_create_products_metadata_success(self, db):
        """Test crear metadatos de producto exitosamente."""
        from django.contrib.contenttypes.models import ContentType
        
        location = Location.objects.create(
            name="Test",
            country="Test",
            type="city"
        )
        
        supplier = Suppliers.objects.create(
            first_name="Test",
            last_name="Supplier",
            organization_name="Test Org",
            description="Test",
            street="Test",
            street_number=123,
            city="Test",
            country="Test",
            email="test@test.com",
            telephone="123456789",
            website="https://test.com"
        )
        
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test",
            location=location,
            date=date.today(),
            start_time=time(10, 0),
            duration_hours=3,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        content_type = ContentType.objects.get_for_model(activity)
        
        metadata = ProductsMetadata.objects.create(
            supplier=supplier,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            content_type_id=content_type,
            object_id=activity.id,
            unit_price=Decimal("150.00"),
            currency="USD"
        )
        
        assert metadata.id is not None
        assert metadata.supplier == supplier
        assert metadata.content == activity
        assert metadata.unit_price == Decimal("150.00")
        assert metadata.is_active is True

    @pytest.mark.unit
    def test_products_metadata_product_type_property(self, db):
        """Test propiedad product_type de metadatos."""
        from django.contrib.contenttypes.models import ContentType
        
        location = Location.objects.create(
            name="Test",
            country="Test",
            type="city"
        )
        
        supplier = Suppliers.objects.create(
            first_name="Test",
            last_name="Supplier",
            organization_name="Test Org",
            description="Test",
            street="Test",
            street_number=123,
            city="Test",
            country="Test",
            email="test@test.com",
            telephone="123456789",
            website="https://test.com"
        )
        
        activity = Activities.objects.create(
            name="Test Activity",
            description="Test",
            location=location,
            date=date.today(),
            start_time=time(10, 0),
            duration_hours=3,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Spanish",
            available_slots=20
        )
        
        content_type = ContentType.objects.get_for_model(activity)
        
        metadata = ProductsMetadata.objects.create(
            supplier=supplier,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            content_type_id=content_type,
            object_id=activity.id,
            unit_price=Decimal("150.00"),
            currency="USD"
        )
        
        assert metadata.product_type == "activity"


class TestPackages:
    """Tests para el modelo Packages."""
    
    @pytest.mark.unit
    def test_create_package_success(self, db):
        """Test crear un paquete exitosamente."""
        category = Category.objects.create(
            name="Aventura",
            description="Paquetes de aventura",
            icon="adventure"
        )
        
        package = Packages.objects.create(
            name="Paquete Aventura Patagonia",
            description="Aventura completa en la Patagonia",
            category=category,
            cover_image="https://example.com/image.jpg",
            base_price=Decimal("500.00"),
            taxes=Decimal("50.00"),
            final_price=Decimal("550.00"),
            rating_average=Decimal("4.5"),
            total_reviews=10
        )
        
        assert package.id is not None
        assert package.name == "Paquete Aventura Patagonia"
        assert package.category == category
        assert package.final_price == Decimal("550.00")
        assert package.rating_average == Decimal("4.5")
        assert package.is_active is True

    @pytest.mark.unit
    def test_package_rating_validation(self, db):
        """Test validación de rating del paquete."""
        category = Category.objects.create(
            name="Test",
            description="Test",
            icon="test"
        )
        
        # Rating válido
        package = Packages.objects.create(
            name="Test Package",
            description="Test",
            category=category,
            final_price=Decimal("100.00"),
            rating_average=Decimal("4.5")
        )
        assert package.rating_average == Decimal("4.5")
        
        # Rating inválido (debería fallar)
        with pytest.raises(ValidationError):
            Packages.objects.create(
                name="Test Package Invalid",
                description="Test",
                category=category,
                final_price=Decimal("100.00"),
                rating_average=Decimal("6.0")  # Inválido (máximo 5.0)
            )

    @pytest.mark.unit
    def test_package_duration_days_property(self, db):
        """Test propiedad duration_days del paquete."""
        category = Category.objects.create(
            name="Test",
            description="Test",
            icon="test"
        )
        
        package = Packages.objects.create(
            name="Test Package",
            description="Test",
            category=category,
            final_price=Decimal("100.00")
        )
        
        # Sin componentes, duración debería ser 0
        assert package.duration_days == 0


class TestStockAuditLog:
    """Tests para el modelo StockAuditLog."""
    
    @pytest.mark.unit
    def test_create_stock_audit_log_success(self, db):
        """Test crear log de auditoría de stock exitosamente."""
        audit_log = StockAuditLog.objects.create(
            operation_type="reserve",
            product_type="activity",
            product_id=123,
            quantity=5,
            previous_stock=20,
            new_stock=15,
            user_id=1,
            session_id="session123",
            request_id="request456",
            metadata={"source": "api"},
            success=True
        )
        
        assert audit_log.id is not None
        assert audit_log.operation_type == "reserve"
        assert audit_log.product_type == "activity"
        assert audit_log.quantity == 5
        assert audit_log.previous_stock == 20
        assert audit_log.new_stock == 15
        assert audit_log.success is True

    @pytest.mark.unit
    def test_stock_audit_log_operation(self, db):
        """Test método log_operation del log de auditoría."""
        # Crear log usando el método de clase
        audit_log = StockAuditLog.log_operation(
            operation_type="reserve",
            product_type="activity",
            product_id=123,
            quantity=5,
            previous_stock=20,
            new_stock=15,
            user_id=1,
            session_id="session123",
            request_id="request456",
            metadata={"source": "api"},
            success=True
        )
        
        assert audit_log.id is not None
        assert audit_log.operation_type == "reserve"
        assert audit_log.success is True
        
        # Verificar que se guardó en la base de datos
        saved_log = StockAuditLog.objects.get(id=audit_log.id)
        assert saved_log.operation_type == "reserve"
        assert saved_log.quantity == 5


class TestStockMetrics:
    """Tests para el modelo StockMetrics."""
    
    @pytest.mark.unit
    def test_create_stock_metrics_success(self, db):
        """Test crear métricas de stock exitosamente."""
        metrics = StockMetrics.objects.create(
            product_type="activity",
            product_id=123,
            total_capacity=100,
            current_reserved=30,
            current_available=70,
            utilization_rate=Decimal("30.00"),
            total_reservations=50,
            total_releases=20,
            failed_operations=2,
            date=date.today()
        )
        
        assert metrics.id is not None
        assert metrics.product_type == "activity"
        assert metrics.total_capacity == 100
        assert metrics.current_reserved == 30
        assert metrics.current_available == 70
        assert metrics.utilization_rate == Decimal("30.00")
        assert metrics.total_reservations == 50

    @pytest.mark.unit
    def test_stock_metrics_update_metrics(self, db):
        """Test método update_metrics de métricas de stock."""
        # Crear métricas usando el método de clase
        metrics = StockMetrics.update_metrics(
            product_type="activity",
            product_id=123,
            total_capacity=100,
            current_reserved=30,
            current_available=70,
            date=date.today()
        )
        
        assert metrics.id is not None
        assert metrics.total_capacity == 100
        assert metrics.current_reserved == 30
        assert metrics.current_available == 70
        assert metrics.utilization_rate == Decimal("30.00")  # 30/100 * 100
        
        # Actualizar las mismas métricas (debería actualizar el registro existente)
        updated_metrics = StockMetrics.update_metrics(
            product_type="activity",
            product_id=123,
            total_capacity=100,
            current_reserved=50,
            current_available=50,
            date=date.today()
        )
        
        assert updated_metrics.id == metrics.id  # Mismo registro
        assert updated_metrics.current_reserved == 50
        assert updated_metrics.utilization_rate == Decimal("50.00")  # 50/100 * 100 