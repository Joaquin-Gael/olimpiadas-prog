#!/usr/bin/env python3
"""
Script para crear datos de prueba para el sistema
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, date, time, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.users.models import Users
from api.products.models import (
    ProductsMetadata, Suppliers, Activities, Location, 
    ActivityAvailability, Flights, Lodgments, Transportation
)
from api.store.models import Cart, CartItem
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

def create_test_users():
    """Crea usuarios de prueba"""
    print("👥 Creando usuarios de prueba...")
    
    # Crear usuario admin
    admin_user, created = Users.objects.get_or_create(
        email="admin@test.com",
        defaults={
            "first_name": "Admin",
            "last_name": "Test",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True
        }
    )
    
    if created:
        admin_user.set_password("admin123")
        admin_user.save()
        print(f"✅ Usuario admin creado: {admin_user.email}")
    else:
        print(f"✅ Usuario admin ya existe: {admin_user.email}")
    
    # Crear usuario normal
    normal_user, created = Users.objects.get_or_create(
        email="user@test.com",
        defaults={
            "first_name": "Usuario",
            "last_name": "Test",
            "is_active": True
        }
    )
    
    if created:
        normal_user.set_password("user123")
        normal_user.save()
        print(f"✅ Usuario normal creado: {normal_user.email}")
    else:
        print(f"✅ Usuario normal ya existe: {normal_user.email}")
    
    return admin_user, normal_user

def create_test_locations():
    """Crea ubicaciones de prueba"""
    print("📍 Creando ubicaciones de prueba...")
    
    # Crear ubicaciones
    locations = [
        {"name": "Buenos Aires", "country": "Argentina", "state": "Buenos Aires", "city": "Buenos Aires", "type": "city"},
        {"name": "Córdoba", "country": "Argentina", "state": "Córdoba", "city": "Córdoba", "type": "city"},
        {"name": "Mendoza", "country": "Argentina", "state": "Mendoza", "city": "Mendoza", "type": "city"},
        {"name": "Bariloche", "country": "Argentina", "state": "Río Negro", "city": "San Carlos de Bariloche", "type": "city"},
    ]
    
    created_locations = []
    for loc_data in locations:
        location, created = Location.objects.get_or_create(
            name=loc_data["name"],
            defaults=loc_data
        )
        if created:
            print(f"✅ Ubicación creada: {location.name}")
        else:
            print(f"✅ Ubicación ya existe: {location.name}")
        created_locations.append(location)
    
    return created_locations

def create_test_suppliers():
    """Crea proveedores de prueba"""
    print("🏢 Creando proveedores de prueba...")
    
    suppliers = [
        {"organization_name": "Turismo Argentina", "contact_email": "info@turismoar.com"},
        {"organization_name": "Aventuras Córdoba", "contact_email": "info@aventurascba.com"},
        {"organization_name": "Mendoza Tours", "contact_email": "info@mendozatours.com"},
    ]
    
    created_suppliers = []
    for sup_data in suppliers:
        supplier, created = Suppliers.objects.get_or_create(
            organization_name=sup_data["organization_name"],
            defaults=sup_data
        )
        if created:
            print(f"✅ Proveedor creado: {supplier.organization_name}")
        else:
            print(f"✅ Proveedor ya existe: {supplier.organization_name}")
        created_suppliers.append(supplier)
    
    return created_suppliers

def create_test_activities(locations, suppliers):
    """Crea actividades de prueba"""
    print("🎯 Creando actividades de prueba...")
    
    activities_data = [
        {
            "name": "City Tour Buenos Aires",
            "description": "Recorrido por los principales puntos turísticos de Buenos Aires",
            "location": locations[0],
            "supplier": suppliers[0],
            "date": date.today() + timedelta(days=7),
            "start_time": time(9, 0),
            "duration_hours": 4,
            "include_guide": True,
            "maximum_spaces": 20,
            "difficulty_level": "Fácil",
            "language": "Español",
            "available_slots": 20,
            "unit_price": Decimal("50.00")
        },
        {
            "name": "Trekking en Córdoba",
            "description": "Caminata por las sierras de Córdoba",
            "location": locations[1],
            "supplier": suppliers[1],
            "date": date.today() + timedelta(days=14),
            "start_time": time(8, 0),
            "duration_hours": 6,
            "include_guide": True,
            "maximum_spaces": 15,
            "difficulty_level": "Intermedio",
            "language": "Español",
            "available_slots": 15,
            "unit_price": Decimal("80.00")
        }
    ]
    
    created_activities = []
    for act_data in activities_data:
        # Crear la actividad
        activity = Activities.objects.create(
            name=act_data["name"],
            description=act_data["description"],
            location=act_data["location"],
            date=act_data["date"],
            start_time=act_data["start_time"],
            duration_hours=act_data["duration_hours"],
            include_guide=act_data["include_guide"],
            maximum_spaces=act_data["maximum_spaces"],
            difficulty_level=act_data["difficulty_level"],
            language=act_data["language"],
            available_slots=act_data["available_slots"]
        )
        
        # Crear metadata del producto
        content_type = ContentType.objects.get_for_model(Activities)
        metadata = ProductsMetadata.objects.create(
            supplier=act_data["supplier"],
            content_type_id=content_type,
            object_id=activity.id,
            unit_price=act_data["unit_price"],
            currency="USD"
        )
        
        # Crear disponibilidad
        availability = ActivityAvailability.objects.create(
            activity=activity,
            event_date=act_data["date"],
            start_time=act_data["start_time"],
            total_seats=act_data["maximum_spaces"],
            reserved_seats=0,
            price=act_data["unit_price"],
            currency="USD",
            state="active"
        )
        
        print(f"✅ Actividad creada: {activity.name} (ID: {metadata.id})")
        created_activities.append({
            "activity": activity,
            "metadata": metadata,
            "availability": availability
        })
    
    return created_activities

def create_test_carts(users, activities):
    """Crea carritos de prueba"""
    print("🛒 Creando carritos de prueba...")
    
    # Crear carrito para el usuario normal
    user = users[1]  # Usuario normal
    cart, created = Cart.objects.get_or_create(
        user=user,
        status="OPEN",
        defaults={
            "currency": "USD",
            "total": Decimal("0.00"),
            "items_cnt": 0
        }
    )
    
    if created:
        print(f"✅ Carrito creado para {user.email}")
    else:
        print(f"✅ Carrito ya existe para {user.email}")
    
    # Agregar items al carrito si hay actividades disponibles
    if activities:
        activity_data = activities[0]  # Primera actividad
        
        # Crear item del carrito
        cart_item = CartItem.objects.create(
            cart=cart,
            availability_id=activity_data["availability"].id,
            product_metadata_id=activity_data["metadata"].id,
            qty=2,
            unit_price=activity_data["metadata"].unit_price,
            currency="USD",
            config={"date": str(activity_data["activity"].date)}
        )
        
        # Recalcular totales del carrito
        cart.total = cart_item.qty * cart_item.unit_price
        cart.items_cnt = cart_item.qty
        cart.save()
        
        print(f"✅ Item agregado al carrito: {cart_item.qty} x {activity_data['activity'].name}")
        print(f"   Total del carrito: ${cart.total}")
    
    return cart

def main():
    """Función principal"""
    print("🚀 Creando datos de prueba...")
    
    try:
        # 1. Crear usuarios
        admin_user, normal_user = create_test_users()
        
        # 2. Crear ubicaciones
        locations = create_test_locations()
        
        # 3. Crear proveedores
        suppliers = create_test_suppliers()
        
        # 4. Crear actividades
        activities = create_test_activities(locations, suppliers)
        
        # 5. Crear carritos
        cart = create_test_carts([admin_user, normal_user], activities)
        
        print("\n✅ Datos de prueba creados exitosamente!")
        print(f"👥 Usuarios: {Users.objects.count()}")
        print(f"📍 Ubicaciones: {Location.objects.count()}")
        print(f"🏢 Proveedores: {Suppliers.objects.count()}")
        print(f"🎯 Actividades: {Activities.objects.count()}")
        print(f"📦 Productos: {ProductsMetadata.objects.count()}")
        print(f"🛒 Carritos: {Cart.objects.count()}")
        print(f"📝 Items en carrito: {CartItem.objects.count()}")
        
        print("\n🔑 Credenciales de acceso:")
        print("   Admin: admin@test.com / admin123")
        print("   User: user@test.com / user123")
        
    except Exception as e:
        print(f"❌ Error creando datos de prueba: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 