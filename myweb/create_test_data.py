#!/usr/bin/env python3
"""
Script para crear datos de prueba básicos para el endpoint GET de productos
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from api.products.models import (
    ProductsMetadata, Activities, Location, Suppliers, 
    ActivityAvailability, DifficultyLevel
)

def log(message):
    """Función para logging con timestamp"""
    timestamp = datetime.now().strftime("[%H:%M:%S]")
    print(f"{timestamp} INFO: {message}")

def create_test_data():
    """Crear datos de prueba básicos"""
    log("🔧 Creando datos de prueba para el endpoint GET de productos...")
    
    try:
        # 1. Crear ubicación
        location, created = Location.objects.get_or_create(
            name="Buenos Aires",
            defaults={
                'country': 'Argentina',
                'state': 'Buenos Aires',
                'city': 'Buenos Aires',
                'type': 'city'
            }
        )
        if created:
            log("✅ Ubicación creada: Buenos Aires")
        else:
            log("✅ Ubicación existente: Buenos Aires")
        
        # 2. Crear proveedor
        supplier, created = Suppliers.objects.get_or_create(
            organization_name="Turismo Test S.A.",
            defaults={
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'description': 'Proveedor de servicios turísticos de prueba',
                'street': 'Av. Corrientes',
                'street_number': 1234,
                'city': 'Buenos Aires',
                'country': 'Argentina',
                'telephone': '+54 11 1234-5678',
                'website': 'https://turismotest.com'
            }
        )
        if created:
            log("✅ Proveedor creado: Turismo Test S.A.")
        else:
            log("✅ Proveedor existente: Turismo Test S.A.")
        
        # 3. Crear actividad
        activity, created = Activities.objects.get_or_create(
            name="City Tour Buenos Aires",
            defaults={
                'description': 'Recorrido turístico por los principales puntos de interés de Buenos Aires',
                'location': location,
                'date': datetime.now().date() + timedelta(days=7),
                'start_time': datetime.strptime('09:00', '%H:%M').time(),
                'duration_hours': 4,
                'include_guide': True,
                'maximum_spaces': 20,
                'difficulty_level': DifficultyLevel.EASY.value,
                'language': 'Español',
                'available_slots': 20
            }
        )
        if created:
            log("✅ Actividad creada: City Tour Buenos Aires")
        else:
            log("✅ Actividad existente: City Tour Buenos Aires")
        
        # 4. Crear disponibilidad de actividad
        availability, created = ActivityAvailability.objects.get_or_create(
            activity=activity,
            event_date=datetime.now().date() + timedelta(days=7),
            defaults={
                'start_time': datetime.strptime('09:00', '%H:%M').time(),
                'total_seats': 20,
                'reserved_seats': 5,
                'price': 50.00,
                'currency': 'USD',
                'state': 'active'
            }
        )
        if created:
            log("✅ Disponibilidad creada para la actividad")
        else:
            log("✅ Disponibilidad existente para la actividad")
        
        # 5. Crear metadata del producto
        content_type = ContentType.objects.get_for_model(Activities)
        metadata, created = ProductsMetadata.objects.get_or_create(
            content_type_id=content_type,
            object_id=activity.id,
            defaults={
                'supplier': supplier,
                'start_date': activity.date,
                'end_date': activity.date,
                'unit_price': 50.00,
                'currency': 'USD',
                'is_active': True
            }
        )
        if created:
            log("✅ Metadata de producto creada")
        else:
            log("✅ Metadata de producto existente")
        
        # 6. Verificar que todo esté correcto
        total_products = ProductsMetadata.objects.active().count()
        log(f"📊 Total de productos activos: {total_products}")
        
        # Verificar serialización
        try:
            from api.products.views_products import serialize_product_metadata
            serialized = serialize_product_metadata(metadata)
            log("✅ Serialización exitosa")
            log(f"   - ID: {serialized['id']}")
            log(f"   - Tipo: {serialized['product_type']}")
            log(f"   - Precio: {serialized['unit_price']}")
        except Exception as e:
            log(f"❌ Error en serialización: {str(e)}")
        
        log("✅ Datos de prueba creados exitosamente")
        return True
        
    except Exception as e:
        log(f"❌ Error creando datos de prueba: {str(e)}")
        return False

def cleanup_test_data():
    """Limpiar datos de prueba"""
    log("🧹 Limpiando datos de prueba...")
    
    try:
        # Eliminar metadata
        ProductsMetadata.objects.filter(
            supplier__organization_name="Turismo Test S.A."
        ).delete()
        
        # Eliminar disponibilidades
        ActivityAvailability.objects.filter(
            activity__name="City Tour Buenos Aires"
        ).delete()
        
        # Eliminar actividad
        Activities.objects.filter(
            name="City Tour Buenos Aires"
        ).delete()
        
        # Eliminar proveedor
        Suppliers.objects.filter(
            organization_name="Turismo Test S.A."
        ).delete()
        
        # Nota: No eliminamos la ubicación porque podría estar en uso por otros datos
        
        log("✅ Datos de prueba limpiados")
        return True
        
    except Exception as e:
        log(f"❌ Error limpiando datos: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_test_data()
    else:
        create_test_data() 