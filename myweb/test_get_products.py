#!/usr/bin/env python
"""
Script independiente para testear el endpoint GET de productos
Ejecutar con: python test_get_products.py
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

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, time, datetime, timedelta
import time as time_module

from api.products.models import (
    ProductsMetadata, Suppliers, Activities, Flights, Lodgments, 
    Transportation, Location, Room, RoomAvailability, ActivityAvailability,
    TransportationAvailability
)
from api.products.services.helpers import serialize_product_metadata
from api.core.querysets import ProductsMetadataQuerySet

User = get_user_model()


class GetProductsTestRunner:
    """
    Runner independiente para tests del GET de productos
    """
    
    def __init__(self):
        self.client = APIClient()
        self.test_data = {}
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def setup_test_data(self):
        """Crear datos de prueba"""
        self.log("Configurando datos de prueba...")
        
        try:
            # Crear ubicaciones
            self.test_data['location1'] = Location.objects.create(
                name="Buenos Aires",
                country="Argentina",
                state="Buenos Aires",
                city="Buenos Aires",
                code="BUE",
                type="city"
            )
            
            self.test_data['location2'] = Location.objects.create(
                name="Córdoba",
                country="Argentina", 
                state="Córdoba",
                city="Córdoba",
                code="COR",
                type="city"
            )
            
            # Crear proveedor
            self.test_data['supplier'] = Suppliers.objects.create(
                first_name="Juan",
                last_name="Pérez",
                organization_name="Turismo Test",
                description="Empresa de turismo de prueba",
                street="Av. Test",
                street_number=123,
                city="Buenos Aires",
                country="Argentina",
                email="test@turismo.com",
                telephone="+54 11 1234-5678",
                website="https://test.com"
            )
            
            # Crear productos
            self.create_test_products()
            
            self.log("✅ Datos de prueba creados exitosamente")
            
        except Exception as e:
            self.log(f"❌ Error creando datos de prueba: {str(e)}", "ERROR")
            raise
    
    def create_test_products(self):
        """Crear productos de prueba"""
        
        # Actividad
        activity = Activities.objects.create(
            name="City Tour Buenos Aires",
            description="Recorrido por los principales puntos de la ciudad",
            location=self.test_data['location1'],
            date=date.today() + timedelta(days=7),
            start_time=time(9, 0),
            duration_hours=3,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Español",
            available_slots=15
        )
        
        self.test_data['activity_metadata'] = ProductsMetadata.objects.create(
            supplier=self.test_data['supplier'],
            content_type_id=activity.get_content_type(),
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
        
        # Vuelo
        flight = Flights.objects.create(
            airline="Aerolíneas Test",
            flight_number="AT123",
            origin=self.test_data['location1'],
            destination=self.test_data['location2'],
            departure_date=date.today() + timedelta(days=1),
            arrival_date=date.today() + timedelta(days=1),
            duration_hours=1,
            departure_time=time(10, 0),
            arrival_time=time(11, 0),
            class_flight="Economy",
            available_seats=150,
            capacity=180,
            luggage_info="1 maleta de 23kg",
            aircraft_type="Boeing 737"
        )
        
        self.test_data['flight_metadata'] = ProductsMetadata.objects.create(
            supplier=self.test_data['supplier'],
            content_type_id=flight.get_content_type(),
            object_id=flight.id,
            unit_price=Decimal("200.00"),
            currency="USD"
        )
        
        # Alojamiento
        lodgment = Lodgments.objects.create(
            name="Hotel Test",
            description="Hotel de prueba en el centro",
            location=self.test_data['location1'],
            type="hotel",
            max_guests=4,
            contact_phone="+54 11 1234-5678",
            contact_email="info@hoteltest.com",
            amenities=["wifi", "parking", "restaurant"],
            date_checkin=date.today() + timedelta(days=1),
            date_checkout=date.today() + timedelta(days=3)
        )
        
        self.test_data['lodgment_metadata'] = ProductsMetadata.objects.create(
            supplier=self.test_data['supplier'],
            content_type_id=lodgment.get_content_type(),
            object_id=lodgment.id,
            unit_price=Decimal("100.00"),
            currency="USD"
        )
        
        room = Room.objects.create(
            lodgment=lodgment,
            room_type="double",
            name="Habitación 101",
            description="Habitación doble con vista a la ciudad",
            capacity=2,
            has_private_bathroom=True,
            has_balcony=True,
            has_air_conditioning=True,
            has_wifi=True,
            base_price_per_night=Decimal("100.00"),
            currency="USD"
        )
        
        RoomAvailability.objects.create(
            room=room,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            available_quantity=1,
            max_quantity=1,
            price_override=None,
            currency="USD",
            is_blocked=False,
            minimum_stay=1
        )
        
        # Transporte
        transportation = Transportation.objects.create(
            origin=self.test_data['location1'],
            destination=self.test_data['location2'],
            type="bus",
            description="Servicio de bus interurbano",
            notes="Salida desde terminal central",
            capacity=50,
            is_active=True
        )
        
        self.test_data['transportation_metadata'] = ProductsMetadata.objects.create(
            supplier=self.test_data['supplier'],
            content_type_id=transportation.get_content_type(),
            object_id=transportation.id,
            unit_price=Decimal("25.00"),
            currency="USD"
        )
        
        TransportationAvailability.objects.create(
            transportation=transportation,
            departure_date=date.today() + timedelta(days=1),
            departure_time=time(8, 0),
            arrival_date=date.today() + timedelta(days=1),
            arrival_time=time(10, 0),
            total_seats=50,
            reserved_seats=10,
            price=Decimal("25.00"),
            currency="USD",
            state="active"
        )
    
    def test_get_products_list(self):
        """Test del endpoint GET /products/"""
        self.log("🧪 Test: GET /products/ - Lista de productos")
        
        try:
            start_time = time_module.time()
            response = self.client.get('/api/products/')
            response_time = time_module.time() - start_time
            
            self.log(f"Status Code: {response.status_code}")
            self.log(f"Tiempo de respuesta: {response_time:.3f}s")
            
            # Verificar respuesta exitosa
            if response.status_code != status.HTTP_200_OK:
                raise AssertionError(f"Status code incorrecto: {response.status_code}")
            
            # Verificar estructura
            data = response.data
            if hasattr(data, 'get'):
                results = data.get('results', [])
                count = data.get('count', 0)
                self.log(f"Total productos: {count}")
                self.log(f"Productos en página: {len(results)}")
            else:
                results = data
                self.log(f"Productos retornados: {len(results)}")
            
            # Verificar que hay productos
            if len(results) == 0:
                raise AssertionError("No se retornaron productos")
            
            # Verificar estructura de cada producto
            for i, product in enumerate(results[:3]):
                required_fields = ['id', 'unit_price', 'currency', 'product_type', 'product']
                for field in required_fields:
                    if field not in product:
                        raise AssertionError(f"Campo requerido '{field}' no encontrado en producto {i}")
                
                # Verificar tipos de datos
                if not isinstance(product['unit_price'], (int, float)):
                    raise AssertionError(f"unit_price no es numérico en producto {i}")
                
                if not isinstance(product['product'], dict):
                    raise AssertionError(f"product no es un diccionario en producto {i}")
            
            self.log("✅ Test GET /products/ exitoso")
            self.results['passed'] += 1
            
        except Exception as e:
            self.log(f"❌ Test GET /products/ falló: {str(e)}", "ERROR")
            self.results['failed'] += 1
            self.results['errors'].append(f"GET /products/: {str(e)}")
    
    def test_get_products_individual(self):
        """Test del endpoint GET /products/{id}/"""
        self.log("🧪 Test: GET /products/{id}/ - Producto individual")
        
        test_cases = [
            (self.test_data['activity_metadata'].id, "activity"),
            (self.test_data['flight_metadata'].id, "flight"),
            (self.test_data['lodgment_metadata'].id, "lodgment"),
            (self.test_data['transportation_metadata'].id, "transportation")
        ]
        
        for metadata_id, expected_type in test_cases:
            try:
                self.log(f"  Probando {expected_type} (ID: {metadata_id})")
                
                response = self.client.get(f'/api/products/{metadata_id}/')
                
                if response.status_code != status.HTTP_200_OK:
                    raise AssertionError(f"Status code incorrecto para {expected_type}: {response.status_code}")
                
                product = response.data
                required_fields = ['id', 'unit_price', 'currency', 'product_type', 'product']
                for field in required_fields:
                    if field not in product:
                        raise AssertionError(f"Campo requerido '{field}' no encontrado en {expected_type}")
                
                if product['product_type'] != expected_type:
                    raise AssertionError(f"Tipo incorrecto para {expected_type}: {product['product_type']}")
                
                self.log(f"  ✅ {expected_type} verificado correctamente")
                
            except Exception as e:
                self.log(f"  ❌ Error en {expected_type}: {str(e)}", "ERROR")
                self.results['failed'] += 1
                self.results['errors'].append(f"GET /products/{metadata_id}/: {str(e)}")
                continue
        
        self.results['passed'] += 1
    
    def test_get_products_test_endpoint(self):
        """Test del endpoint de diagnóstico"""
        self.log("🧪 Test: GET /products/test/ - Endpoint de diagnóstico")
        
        try:
            response = self.client.get('/api/products/test/')
            
            if response.status_code != status.HTTP_200_OK:
                raise AssertionError(f"Status code incorrecto: {response.status_code}")
            
            data = response.data
            required_fields = ['status', 'total_active_products', 'by_type', 'available_products', 'products_with_issues']
            for field in required_fields:
                if field not in data:
                    raise AssertionError(f"Campo requerido '{field}' no encontrado")
            
            if data['status'] != 'success':
                raise AssertionError(f"Status incorrecto: {data['status']}")
            
            self.log(f"Total productos activos: {data['total_active_products']}")
            self.log(f"Productos por tipo: {data['by_type']}")
            self.log(f"Productos disponibles: {data['available_products']}")
            self.log(f"Productos con problemas: {len(data['products_with_issues'])}")
            
            if len(data['products_with_issues']) > 0:
                self.log(f"⚠️  Productos con problemas encontrados: {data['products_with_issues']}", "WARNING")
            
            self.log("✅ Test endpoint de diagnóstico exitoso")
            self.results['passed'] += 1
            
        except Exception as e:
            self.log(f"❌ Test endpoint de diagnóstico falló: {str(e)}", "ERROR")
            self.results['failed'] += 1
            self.results['errors'].append(f"GET /products/test/: {str(e)}")
    
    def test_serialize_function(self):
        """Test directo de la función de serialización"""
        self.log("🧪 Test: Función serialize_product_metadata")
        
        test_cases = [
            (self.test_data['activity_metadata'], "activity"),
            (self.test_data['flight_metadata'], "flight"),
            (self.test_data['lodgment_metadata'], "lodgment"),
            (self.test_data['transportation_metadata'], "transportation")
        ]
        
        for metadata, expected_type in test_cases:
            try:
                result = serialize_product_metadata(metadata)
                
                required_fields = ['id', 'unit_price', 'currency', 'product_type', 'product']
                for field in required_fields:
                    if field not in result:
                        raise AssertionError(f"Campo requerido '{field}' no encontrado en {expected_type}")
                
                if result['product_type'] != expected_type:
                    raise AssertionError(f"Tipo incorrecto para {expected_type}: {result['product_type']}")
                
                if not isinstance(result['unit_price'], float):
                    raise AssertionError(f"unit_price no es float en {expected_type}")
                
                self.log(f"  ✅ {expected_type} serializado correctamente")
                
            except Exception as e:
                self.log(f"  ❌ Error serializando {expected_type}: {str(e)}", "ERROR")
                self.results['failed'] += 1
                self.results['errors'].append(f"serialize_product_metadata {expected_type}: {str(e)}")
                continue
        
        self.results['passed'] += 1
    
    def test_queryset_available_only(self):
        """Test del queryset available_only"""
        self.log("🧪 Test: Queryset available_only")
        
        try:
            available_products = ProductsMetadata.objects.active().available_only()
            count = available_products.count()
            
            self.log(f"Productos disponibles: {count}")
            
            if count == 0:
                raise AssertionError("No hay productos disponibles")
            
            # Verificar que se puede acceder al contenido
            for product in available_products[:3]:
                if not hasattr(product, 'content') or product.content is None:
                    raise AssertionError(f"Producto {product.id} no tiene contenido válido")
            
            self.log("✅ Queryset available_only funcionando correctamente")
            self.results['passed'] += 1
            
        except Exception as e:
            self.log(f"❌ Test queryset available_only falló: {str(e)}", "ERROR")
            self.results['failed'] += 1
            self.results['errors'].append(f"queryset available_only: {str(e)}")
    
    def cleanup_test_data(self):
        """Limpiar datos de prueba"""
        self.log("🧹 Limpiando datos de prueba...")
        
        try:
            # Eliminar en orden inverso para evitar problemas de dependencias
            ProductsMetadata.objects.all().delete()
            TransportationAvailability.objects.all().delete()
            RoomAvailability.objects.all().delete()
            ActivityAvailability.objects.all().delete()
            Room.objects.all().delete()
            Transportation.objects.all().delete()
            Flights.objects.all().delete()
            Activities.objects.all().delete()
            Lodgments.objects.all().delete()
            Suppliers.objects.all().delete()
            Location.objects.all().delete()
            
            self.log("✅ Datos de prueba limpiados")
            
        except Exception as e:
            self.log(f"⚠️  Error limpiando datos: {str(e)}", "WARNING")
    
    def run_all_tests(self):
        """Ejecutar todos los tests"""
        self.log("🚀 Iniciando tests del endpoint GET de productos...")
        self.log("=" * 60)
        
        try:
            # Setup
            self.setup_test_data()
            
            # Ejecutar tests
            self.test_get_products_list()
            self.test_get_products_individual()
            self.test_get_products_test_endpoint()
            self.test_serialize_function()
            self.test_queryset_available_only()
            
        except Exception as e:
            self.log(f"❌ Error crítico durante los tests: {str(e)}", "ERROR")
            self.results['failed'] += 1
            self.results['errors'].append(f"Error crítico: {str(e)}")
        
        finally:
            # Cleanup
            self.cleanup_test_data()
        
        # Mostrar resultados
        self.log("=" * 60)
        self.log("📊 RESULTADOS FINALES:")
        self.log(f"✅ Tests exitosos: {self.results['passed']}")
        self.log(f"❌ Tests fallidos: {self.results['failed']}")
        
        if self.results['errors']:
            self.log("🔍 ERRORES DETECTADOS:")
            for error in self.results['errors']:
                self.log(f"  - {error}", "ERROR")
        
        total_tests = self.results['passed'] + self.results['failed']
        if total_tests > 0:
            success_rate = (self.results['passed'] / total_tests) * 100
            self.log(f"📈 Tasa de éxito: {success_rate:.1f}%")
        
        if self.results['failed'] == 0:
            self.log("🎉 ¡Todos los tests pasaron exitosamente!")
        else:
            self.log("⚠️  Algunos tests fallaron. Revisar errores arriba.")


if __name__ == '__main__':
    # Ejecutar tests
    runner = GetProductsTestRunner()
    runner.run_all_tests() 