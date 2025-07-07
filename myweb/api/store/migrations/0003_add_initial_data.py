from django.db import migrations
from decimal import Decimal
from django.utils import timezone

def create_initial_store_data(apps, schema_editor):
    Users = apps.get_model('users', 'Users')
    Packages = apps.get_model('products', 'Packages')
    Suppliers = apps.get_model('products', 'Suppliers')
    ProductsMetadata = apps.get_model('products', 'ProductsMetadata')
    ComponentPackages = apps.get_model('products', 'ComponentPackages')
    Cart = apps.get_model('store', 'Cart')
    CartItem = apps.get_model('store', 'CartItem')
    Orders = apps.get_model('store', 'Orders')
    OrderDetails = apps.get_model('store', 'OrderDetails')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Activities = apps.get_model('products', 'Activities')
    ActivityAvailability = apps.get_model('products', 'ActivityAvailability')
    Location = apps.get_model('products', 'Location')

    # Hash de '1234' generado por Django 4.x pbkdf2_sha256
    password_hash = 'pbkdf2_sha256$600000$wQn6QwQwQwQw$QwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQw=='

    user = Users.objects.filter(email='testuser@example.com').first()
    if not user:
        user = Users.objects.filter(telephone='123456789').first()
    if not user:
        user = Users.objects.create(
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            telephone='123456789',
            password=password_hash
        )

    # Crear un Location y Supplier de prueba si no existen
    location = Location.objects.create(name="Ciudad Test", country="Testland", state="", city="Ciudad Test", code="TST", type="city")
    supplier = Suppliers.objects.create(first_name="Test", last_name="Supplier", organization_name="TestOrg", description="", street="Calle", street_number=1, city="Ciudad Test", country="Testland", email="proveedor@test.com", telephone="123456", website="https://test.com")

    # 1. Crear una actividad
    activity = Activities.objects.create(
        name="Simulada",
        description="Actividad de prueba",
        location=location,
        date="2024-06-20",
        start_time="10:00",
        duration_hours=2,
        include_guide=True,
        maximum_spaces=20,
        difficulty_level="EASY",
        language="es",
        available_slots=20,
        is_active=True
    )

    # 2. Crear una disponibilidad para esa actividad
    availability = ActivityAvailability.objects.create(
        activity=activity,
        event_date="2024-06-20",
        start_time="10:00",
        total_seats=20,
        reserved_seats=0,
        price=100,
        currency="USD",
        state="active"
    )

    # 3. Crear un paquete
    package = Packages.objects.create(
        name="Paquete Simulado",
        description="Paquete de prueba",
        final_price=1000
    )

    # 4. Crear un ProductsMetadata apuntando a la actividad
    content_type = ContentType.objects.get_for_model(activity)
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        start_date="2024-06-20",
        end_date="2024-06-21",
        content_type_id=content_type,
        object_id=activity.id,
        unit_price=100,
        currency="USD",
        is_active=True
    )

    # 5. Finalmente, crear el ComponentPackages
    ComponentPackages.objects.create(
        package=package,
        product_metadata=metadata,
        availability_id=availability.id,
        order=1,
        quantity=1,
        title="Componente de prueba"
    )

    cart = Cart.objects.create(
        user=user,
        status='OPEN',
        currency='USD',
        total=Decimal('50.00'),
        items_cnt=1
    )

    cart_item = CartItem.objects.create(
        cart=cart,
        availability_id=availability.id,
        product_metadata=metadata,
        qty=1,
        unit_price=Decimal('50.00'),
        currency='USD',
        config={}
    )

    order = Orders.objects.create(
        user=user,
        date=timezone.now(),
        state='PENDING',
        total=Decimal('100.00'),
        idempotency_key='test-key-1'
    )

    order_detail = OrderDetails.objects.create(
        order=order,
        product_metadata=metadata,
        package=package,
        availability_id=availability.id,
        quantity=1,
        unit_price=Decimal('50.00'),
        subtotal=Decimal('50.00'),
        discount_applied=Decimal('0.00')
    )

class Migration(migrations.Migration):
    dependencies = [
        ('store', '0002_initial'),
        ('users', '0001_initial'),
        ('products', '0002_initial'),
    ]
    operations = [
        migrations.RunPython(create_initial_store_data),
    ] 