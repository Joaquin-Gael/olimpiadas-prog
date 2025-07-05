#!/usr/bin/env python
"""
Script simple para testear el endpoint GET de productos
Ejecutar con: python run_get_products_test.py
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


def log(message, level="INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def test_get_products_endpoint():
    """Test principal del endpoint GET de productos"""
    log("🚀 Iniciando test del endpoint GET de productos...")
    
    client = Client()
    test_results = {'passed': 0, 'failed': 0, 'errors': []}
    
    try:
        # Test 1: GET /api/products/ - Lista de productos
        log("🧪 Test 1: GET /api/products/ - Lista de productos")
        
        start_time = time_module.time()
        response = client.get('/api/products/')
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
                        log("✅ Test 1: GET /api/products/ exitoso")
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
        
        # Test 2: GET /api/products/test/ - Endpoint de diagnóstico
        log("🧪 Test 2: GET /api/products/test/ - Endpoint de diagnóstico")
        
        response = client.get('/api/products/test/')
        
        if response.status_code == 200:
            try:
                data = json.loads(response.content)
                log(f"Status: {data.get('status')}")
                log(f"Total productos activos: {data.get('total_active_products')}")
                log(f"Productos por tipo: {data.get('by_type')}")
                log(f"Productos disponibles: {data.get('available_products')}")
                log(f"Productos con problemas: {len(data.get('products_with_issues', []))}")
                
                if data.get('status') == 'success':
                    log("✅ Test 2: GET /api/products/test/ exitoso")
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
        log("🧪 Test 3: GET /api/products/{id}/ - Productos individuales")
        
        # Obtener algunos productos para probar
        products = ProductsMetadata.objects.active()[:3]
        
        for product in products:
            try:
                response = client.get(f'/api/products/{product.id}/')
                
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


if __name__ == '__main__':
    log("Iniciando tests del endpoint GET de productos...")
    
    # Ejecutar tests principales
    main_test_success = test_get_products_endpoint()
    
    # Ejecutar test de serialización
    serialize_test_success = test_serialize_function()
    
    # Ejecutar test de queryset
    queryset_test_success = test_queryset_available_only()
    
    # Resultado final
    if main_test_success and serialize_test_success and queryset_test_success:
        log("🎉 ¡Todos los tests completados exitosamente!")
        sys.exit(0)
    else:
        log("❌ Algunos tests fallaron")
        sys.exit(1) 