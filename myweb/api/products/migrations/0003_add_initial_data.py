from django.db import migrations
from decimal import Decimal
from datetime import date, timedelta, time

def create_initial_products(apps, schema_editor):
    Location = apps.get_model('products', 'Location')
    Suppliers = apps.get_model('products', 'Suppliers')
    Category = apps.get_model('products', 'Category')
    Activities = apps.get_model('products', 'Activities')
    ProductsMetadata = apps.get_model('products', 'ProductsMetadata')
    ActivityAvailability = apps.get_model('products', 'ActivityAvailability')
    Users = apps.get_model('users', 'Users')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # Ubicaciones
    loc1 = Location.objects.create(
        name="Buenos Aires", country="Argentina", state="Buenos Aires", city="Buenos Aires", code="BUE", type="city"
    )
    loc2 = Location.objects.create(
        name="Córdoba", country="Argentina", state="Córdoba", city="Córdoba", code="COR", type="city"
    )

    # Proveedor
    supplier = Suppliers.objects.create(
        first_name="Juan", last_name="Pérez", organization_name="Turismo Test",
        description="Empresa de turismo de prueba", street="Av. Test", street_number=123,
        city="Buenos Aires", country="Argentina", email="test@turismo.com",
        telephone="+54 11 1234-5678", website="https://test.com"
    )

    # Categoría
    category = Category.objects.create(
        name="Aventura", description="Actividades de aventura y deportes extremos", icon="mountain"
    )

    # Usuario
    user = Users.objects.filter(email="test@example.com").first()

    # Actividad
    activity = Activities.objects.create(
        name="City Tour Buenos Aires", description="Recorrido por los principales puntos de la ciudad",
        location=loc1, date=date.today() + timedelta(days=7), start_time=time(9, 0),
        duration_hours=3, include_guide=True, maximum_spaces=20, difficulty_level="Easy",
        language="Español", available_slots=15
    )

    # Obtener ContentType para Activities (usando get_or_create)
    content_type, _ = ContentType.objects.get_or_create(app_label='products', model='activities')

    # Metadata para actividad
    ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=activity.id,
        unit_price=Decimal("50.00"),
        currency="USD"
    )

    # Disponibilidad para actividad
    ActivityAvailability.objects.create(
        activity=activity, event_date=date.today() + timedelta(days=7), start_time=time(9, 0),
        total_seats=20, reserved_seats=5, price=Decimal("50.00"), currency="USD", state="active"
    )

class Migration(migrations.Migration):
    dependencies = [
        ('products', '0002_initial'),
        ('users', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]
    operations = [
        migrations.RunPython(create_initial_products),
    ] 