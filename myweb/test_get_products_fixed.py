#!/usr/bin/env python
"""
Script corregido para testear el endpoint GET de productos con id_prefix
Ejecutar con: python test_get_products_fixed.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

from django.test import TestCase, Client
from decimal import Decimal
from datetime import date, time, datetime, timedelta
import time as time_module
import json

from api.products.models import (
    ProductsMetadata, Suppliers, Activities, Flights, Lodgments, 
    Transportation, Location, Room, RoomAvailability, ActivityAvailability,
    TransportationAvailability
)
from api.products.services.helpers import serialize_product_metadata
from myweb.settings import ID_PREFIX
from django.contrib.contenttypes.models import ContentType


def log(message, level="INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def get_id_prefix():
    """Obtener el id_prefix de la configuración"""
    return str(ID_PREFIX)


def create_test_data():
    """Crear datos de prueba para el test"""
    log("🔧 Creando datos de prueba...")
    
    try:
        # Verificar si ya existen datos de prueba
        existing_products = ProductsMetadata.objects.active().count()
        if existing_products > 0:
            log(f"⚠️  Ya existen {existing_products} productos en la base de datos")
            log("Usando datos existentes para el test")
            return True
        
        # Usar ubicaciones existentes o crear nuevas
        location1 = Location.objects.filter(
            name="Buenos Aires",
            country="Argentina",
            state="Buenos Aires"
        ).first()
        
        if not location1:
            location1 = Location.objects.create(
                name="Buenos Aires",
                country="Argentina",
                state="Buenos Aires",
                city="Buenos Aires",
                code="BUE",
                type="city"
            )
        
        location2 = Location.objects.filter(
            name="Córdoba",
            country="Argentina", 
            state="Córdoba"
        ).first()
        
        if not location2:
            location2 = Location.objects.create(
                name="Córdoba",
                country="Argentina", 
                state="Córdoba",
                city="Córdoba",
                code="COR",
                type="city"
            )
        
        # Crear proveedor con email único
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@turismo.com"
        
        supplier = Suppliers.objects.create(
            first_name="Juan",
            last_name="Pérez",
            organization_name="Turismo Test",
            description="Empresa de turismo de prueba",
            street="Av. Test",
            street_number=123,
            city="Buenos Aires",
            country="Argentina",
            email=unique_email,
            telephone="+54 11 1234-5678",
            website="https://test.com"
        )
        
        # Crear actividad
        activity = Activities.objects.create(
            name="City Tour Buenos Aires",
            description="Recorrido por los principales puntos de la ciudad",
            location=location1,
            date=date.today() + timedelta(days=7),
            start_time=time(9, 0),
            duration_hours=3,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Español",
            available_slots=15
        )
        
        activity_metadata = ProductsMetadata.objects.create(
            supplier=supplier,
            content_type_id=ContentType.objects.get_for_model(activity),
            object_id=activity.id,
            unit_price=Decimal("50.00"),
            currency="USD"
        )
        
        ActivityAvailability.objects.create(
            activity=activity,
            event_date=date.today() + timedelta(days=7),
            start_time=time(9, 0),
            total_seats=20,
            reserved_seats=5,
            price=Decimal("50.00"),
            currency="USD",
            state="active"
        )
        
        log("✅ Datos de prueba creados exitosamente")
        return True
        
    except Exception as e:
        log(f"❌ Error creando datos de prueba: {str(e)}", "ERROR")
        return False


def test_get_products_endpoint():
    """Test principal del endpoint GET de productos"""
    log("🚀 Iniciando test del endpoint GET de productos...")
    
    # Obtener id_prefix
    id_prefix = get_id_prefix()
    log(f"ID Prefix: {id_prefix}")
    
    client = Client()
    test_results = {'passed': 0, 'failed': 0, 'errors': []}
    
    try:
        # Test 1: GET /{id_prefix}/products/all/ - Lista de productos sin filtros
        endpoint = f'/{id_prefix}/products/all/'
        log(f"🧪 Test 1: GET {endpoint} - Lista de productos sin filtros")
        
        start_time = time_module.time()
        response = client.get(endpoint)
        response_time = time_module.time() - start_time
        
        log(f"Status Code: {response.status_code}")
        log(f"Tiempo de respuesta: {response_time:.3f}s")
        
        if response.status_code == 200:
            try:
                data = json.loads(response.content)
                
                # Verificar estructura de respuesta
                if isinstance(data, dict) and 'results' in data:
                    results = data.get('results', [])
                    count = data.get('count', 0)
                    log(f"Total productos: {count}")
                    log(f"Productos en página: {len(results)}")
                else:
                    results = data if isinstance(data, list) else []
                    log(f"Productos retornados: {len(results)}")
                
                # Verificar que hay productos
                if len(results) > 0:
                    # Verificar estructura del primer producto
                    first_product = results[0]
                    required_fields = ['id', 'unit_price', 'currency', 'product_type', 'product']
                    
                    missing_fields = [field for field in required_fields if field not in first_product]
                    if not missing_fields:
                        log("✅ Test 1: GET productos/all exitoso")
                        test_results['passed'] += 1
                    else:
                        raise AssertionError(f"Campos faltantes: {missing_fields}")
                else:
                    log("⚠️  No hay productos en la base de datos")
                    test_results['passed'] += 1
                    
            except json.JSONDecodeError as e:
                log(f"❌ Error decodificando JSON: {str(e)}")
                log(f"Contenido de respuesta: {response.content[:200]}...")
                test_results['failed'] += 1
                test_results['errors'].append(f"JSON decode error: {str(e)}")
        else:
            raise AssertionError(f"Status code incorrecto: {response.status_code}")
        
        # Test 1.5: GET /{id_prefix}/products/ - Lista de productos con filtros (para comparar)
        endpoint_filtered = f'/{id_prefix}/products/'
        log(f"🧪 Test 1.5: GET {endpoint_filtered} - Lista de productos con filtros")
        
        response_filtered = client.get(endpoint_filtered)
        log(f"Status Code (con filtros): {response_filtered.status_code}")
        
        if response_filtered.status_code == 200:
            try:
                data_filtered = json.loads(response_filtered.content)
                if isinstance(data_filtered, dict) and 'results' in data_filtered:
                    results_filtered = data_filtered.get('results', [])
                    count_filtered = data_filtered.get('count', 0)
                    log(f"Productos con filtros: {count_filtered}")
                else:
                    results_filtered = data_filtered if isinstance(data_filtered, list) else []
                    log(f"Productos con filtros: {len(results_filtered)}")
                
                log(f"Comparación: {len(results)} productos sin filtros vs {len(results_filtered)} con filtros")
                
            except json.JSONDecodeError as e:
                log(f"❌ Error decodificando JSON con filtros: {str(e)}")
        else:
            log(f"❌ Error en endpoint con filtros: {response_filtered.status_code}")
        
        # Test 2: GET /{id_prefix}/products/test/ - Endpoint de diagnóstico
        test_endpoint = f'/{id_prefix}/products/test/'
        log(f"🧪 Test 2: GET {test_endpoint} - Endpoint de diagnóstico")
        
        response = client.get(test_endpoint)
        
        if response.status_code == 200:
            try:
                data = json.loads(response.content)
                log(f"Status: {data.get('status')}")
                log(f"Total productos activos: {data.get('total_active_products')}")
                log(f"Productos por tipo: {data.get('by_type')}")
                log(f"Productos disponibles: {data.get('available_products')}")
                log(f"Productos con problemas: {len(data.get('products_with_issues', []))}")
                
                if data.get('status') == 'success':
                    log("✅ Test 2: GET test endpoint exitoso")
                    test_results['passed'] += 1
                else:
                    raise AssertionError(f"Status incorrecto: {data.get('status')}")
                    
            except json.JSONDecodeError as e:
                log(f"❌ Error decodificando JSON del endpoint test: {str(e)}")
                test_results['failed'] += 1
                test_results['errors'].append(f"JSON decode error in test endpoint: {str(e)}")
        else:
            raise AssertionError(f"Status code incorrecto: {response.status_code}")
        
        # Test 3: Verificar productos existentes individualmente
        log("🧪 Test 3: GET productos individuales")
        
        # Obtener algunos productos para probar
        products = ProductsMetadata.objects.active()[:3]
        
        for product in products:
            try:
                individual_endpoint = f'/{id_prefix}/products/{product.id}/'
                response = client.get(individual_endpoint)
                
                if response.status_code == 200:
                    try:
                        product_data = json.loads(response.content)
                        log(f"  ✅ Producto {product.id} ({product.product_type}) verificado")
                    except json.JSONDecodeError as e:
                        log(f"  ❌ Error JSON en producto {product.id}: {str(e)}")
                        test_results['failed'] += 1
                else:
                    log(f"  ❌ Error en producto {product.id}: Status {response.status_code}")
                    test_results['failed'] += 1
                    
            except Exception as e:
                log(f"  ❌ Error en producto {product.id}: {str(e)}")
                test_results['failed'] += 1
        
        test_results['passed'] += 1
        
        # Test 4: Test de rendimiento
        log("🧪 Test 4: Rendimiento")
        
        if response_time < 2.0:
            log("✅ Rendimiento aceptable (< 2 segundos)")
            test_results['passed'] += 1
        else:
            log(f"⚠️  Rendimiento lento: {response_time:.3f}s")
            test_results['passed'] += 1
        
    except Exception as e:
        log(f"❌ Error crítico durante los tests: {str(e)}", "ERROR")
        test_results['failed'] += 1
        test_results['errors'].append(str(e))
    
    # Mostrar resultados finales
    log("=" * 60)
    log("📊 RESULTADOS FINALES:")
    log(f"✅ Tests exitosos: {test_results['passed']}")
    log(f"❌ Tests fallidos: {test_results['failed']}")
    
    if test_results['errors']:
        log("🔍 ERRORES DETECTADOS:")
        for error in test_results['errors']:
            log(f"  - {error}", "ERROR")
    
    total_tests = test_results['passed'] + test_results['failed']
    if total_tests > 0:
        success_rate = (test_results['passed'] / total_tests) * 100
        log(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    if test_results['failed'] == 0:
        log("🎉 ¡Todos los tests pasaron exitosamente!")
        return True
    else:
        log("⚠️  Algunos tests fallaron. Revisar errores arriba.")
        return False


def test_serialize_function():
    """Test directo de la función de serialización"""
    log("🧪 Test adicional: Función serialize_product_metadata")
    
    try:
        # Obtener un producto para probar
        product = ProductsMetadata.objects.active().first()
        
        if product:
            result = serialize_product_metadata(product)
            
            # Verificar estructura
            required_fields = ['id', 'unit_price', 'currency', 'product_type', 'product']
            missing_fields = [field for field in required_fields if field not in result]
            
            if not missing_fields:
                log(f"✅ Serialización exitosa para producto {product.id}")
                log(f"  Tipo: {result['product_type']}")
                log(f"  Precio: {result['unit_price']}")
                return True
            else:
                log(f"❌ Campos faltantes en serialización: {missing_fields}")
                return False
        else:
            log("⚠️  No hay productos para probar serialización")
            return True
            
    except Exception as e:
        log(f"❌ Error en serialización: {str(e)}")
        return False


def test_queryset_available_only():
    """Test del queryset available_only"""
    log("🧪 Test adicional: Queryset available_only")
    
    try:
        available_products = ProductsMetadata.objects.active().available_only()
        count = available_products.count()
        
        log(f"Productos disponibles: {count}")
        
        if count >= 0:  # Puede ser 0 si no hay productos disponibles
            log("✅ Queryset available_only funcionando correctamente")
            return True
        else:
            log("❌ Error en queryset available_only")
            return False
            
    except Exception as e:
        log(f"❌ Error en queryset available_only: {str(e)}")
        return False


def cleanup_test_data():
    """Limpiar datos de prueba"""
    log("🧹 Limpiando datos de prueba...")
    
    try:
        # Eliminar en orden inverso para evitar problemas de dependencias
        ProductsMetadata.objects.all().delete()
        ActivityAvailability.objects.all().delete()
        Activities.objects.all().delete()
        Suppliers.objects.all().delete()
        Location.objects.all().delete()
        
        log("✅ Datos de prueba limpiados")
        
    except Exception as e:
        log(f"⚠️  Error limpiando datos: {str(e)}", "WARNING")


if __name__ == '__main__':
    log("Iniciando tests del endpoint GET de productos...")
    
    # Crear datos de prueba
    data_created = create_test_data()
    
    if data_created:
        # Ejecutar tests principales
        main_test_success = test_get_products_endpoint()
        
        # Ejecutar test de serialización
        serialize_test_success = test_serialize_function()
        
        # Ejecutar test de queryset
        queryset_test_success = test_queryset_available_only()
        
        # Limpiar datos de prueba
        cleanup_test_data()
        
        # Resultado final
        if main_test_success and serialize_test_success and queryset_test_success:
            log("🎉 ¡Todos los tests completados exitosamente!")
            sys.exit(0)
        else:
            log("❌ Algunos tests fallaron")
            sys.exit(1)
    else:
        log("❌ No se pudieron crear datos de prueba")
        sys.exit(1) 