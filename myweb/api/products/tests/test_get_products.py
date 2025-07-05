import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, time, datetime, timedelta
from unittest.mock import patch, MagicMock

from api.products.models import (
    ProductsMetadata, Suppliers, Activities, Flights, Lodgments, 
    Transportation, Location, Room, RoomAvailability, ActivityAvailability,
    TransportationAvailability
)
from api.products.services.helpers import serialize_product_metadata
from api.core.querysets import ProductsMetadataQuerySet

User = get_user_model()


class TestGetProductsEndpoint(TestCase):
    """
    Test suite específico para el endpoint GET de productos
    """
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = APIClient()
        
        # Crear ubicaciones de prueba
        self.location1 = Location.objects.create(
            name="Buenos Aires",
            country="Argentina",
            state="Buenos Aires",
            city="Buenos Aires",
            code="BUE",
            type="city"
        )
        
        self.location2 = Location.objects.create(
            name="Córdoba",
            country="Argentina", 
            state="Córdoba",
            city="Córdoba",
            code="COR",
            type="city"
        )
        
        # Crear proveedor de prueba
        self.supplier = Suppliers.objects.create(
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
        
        # Crear productos de prueba
        self.create_test_products()
    
    def create_test_products(self):
        """Crear productos de prueba de todos los tipos"""
        
        # 1. Actividad de prueba
        self.activity = Activities.objects.create(
            name="City Tour Buenos Aires",
            description="Recorrido por los principales puntos de la ciudad",
            location=self.location1,
            date=date.today() + timedelta(days=7),
            start_time=time(9, 0),
            duration_hours=3,
            include_guide=True,
            maximum_spaces=20,
            difficulty_level="Easy",
            language="Español",
            available_slots=15
        )
        
        # Metadata para actividad
        self.activity_metadata = ProductsMetadata.objects.create(
            supplier=self.supplier,
            content_type_id=self.activity.get_content_type(),
            object_id=self.activity.id,
            unit_price=Decimal("50.00"),
            currency="USD"
        )
        
        # Disponibilidad para actividad
        self.activity_availability = ActivityAvailability.objects.create(
            activity=self.activity,
            event_date=date.today() + timedelta(days=7),
            start_time=time(9, 0),
            total_seats=20,
            reserved_seats=5,
            price=Decimal("50.00"),
            currency="USD",
            state="active"
        )
        
        # 2. Vuelo de prueba
        self.flight = Flights.objects.create(
            airline="Aerolíneas Test",
            flight_number="AT123",
            origin=self.location1,
            destination=self.location2,
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
        
        # Metadata para vuelo
        self.flight_metadata = ProductsMetadata.objects.create(
            supplier=self.supplier,
            content_type_id=self.flight.get_content_type(),
            object_id=self.flight.id,
            unit_price=Decimal("200.00"),
            currency="USD"
        )
        
        # 3. Alojamiento de prueba
        self.lodgment = Lodgments.objects.create(
            name="Hotel Test",
            description="Hotel de prueba en el centro",
            location=self.location1,
            type="hotel",
            max_guests=4,
            contact_phone="+54 11 1234-5678",
            contact_email="info@hoteltest.com",
            amenities=["wifi", "parking", "restaurant"],
            date_checkin=date.today() + timedelta(days=1),
            date_checkout=date.today() + timedelta(days=3)
        )
        
        # Metadata para alojamiento
        self.lodgment_metadata = ProductsMetadata.objects.create(
            supplier=self.supplier,
            content_type_id=self.lodgment.get_content_type(),
            object_id=self.lodgment.id,
            unit_price=Decimal("100.00"),
            currency="USD"
        )
        
        # Habitación para alojamiento
        self.room = Room.objects.create(
            lodgment=self.lodgment,
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
        
        # Disponibilidad para habitación
        self.room_availability = RoomAvailability.objects.create(
            room=self.room,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            available_quantity=1,
            max_quantity=1,
            price_override=None,
            currency="USD",
            is_blocked=False,
            minimum_stay=1
        )
        
        # 4. Transporte de prueba
        self.transportation = Transportation.objects.create(
            origin=self.location1,
            destination=self.location2,
            type="bus",
            description="Servicio de bus interurbano",
            notes="Salida desde terminal central",
            capacity=50,
            is_active=True
        )
        
        # Metadata para transporte
        self.transportation_metadata = ProductsMetadata.objects.create(
            supplier=self.supplier,
            content_type_id=self.transportation.get_content_type(),
            object_id=self.transportation.id,
            unit_price=Decimal("25.00"),
            currency="USD"
        )
        
        # Disponibilidad para transporte
        self.transportation_availability = TransportationAvailability.objects.create(
            transportation=self.transportation,
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
    
    def test_get_products_list_success(self):
        """Test del endpoint GET /products/ - Lista exitosa"""
        print("\n=== Test: GET /products/ - Lista exitosa ===")
        
        # Hacer la petición
        response = self.client.get('/api/products/')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Type: {type(response.data)}")
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data)
        
        # Verificar estructura de respuesta
        if hasattr(response.data, 'get'):
            # Respuesta paginada
            results = response.data.get('results', [])
            count = response.data.get('count', 0)
            print(f"Total productos: {count}")
            print(f"Productos en página: {len(results)}")
        else:
            # Respuesta directa
            results = response.data
            print(f"Productos retornados: {len(results)}")
        
        # Verificar que hay productos
        self.assertGreater(len(results), 0)
        
        # Verificar estructura de cada producto
        for i, product in enumerate(results[:3]):  # Solo los primeros 3
            print(f"\nProducto {i+1}:")
            print(f"  ID: {product.get('id')}")
            print(f"  Tipo: {product.get('product_type')}")
            print(f"  Precio: {product.get('unit_price')}")
            print(f"  Moneda: {product.get('currency')}")
            
            # Verificar campos requeridos
            self.assertIn('id', product)
            self.assertIn('unit_price', product)
            self.assertIn('currency', product)
            self.assertIn('product_type', product)
            self.assertIn('product', product)
            
            # Verificar que el precio es numérico
            self.assertIsInstance(product['unit_price'], (int, float))
            
            # Verificar que el producto tiene datos
            product_data = product.get('product')
            self.assertIsNotNone(product_data)
            self.assertIn('id', product_data)
    
    def test_get_products_individual_success(self):
        """Test del endpoint GET /products/{id}/ - Producto individual"""
        print("\n=== Test: GET /products/{id}/ - Producto individual ===")
        
        # Probar con cada tipo de producto
        test_cases = [
            (self.activity_metadata.id, "activity"),
            (self.flight_metadata.id, "flight"),
            (self.lodgment_metadata.id, "lodgment"),
            (self.transportation_metadata.id, "transportation")
        ]
        
        for metadata_id, expected_type in test_cases:
            print(f"\nProbando producto {expected_type} (ID: {metadata_id}):")
            
            response = self.client.get(f'/api/products/{metadata_id}/')
            
            print(f"  Status Code: {response.status_code}")
            
            # Verificar respuesta exitosa
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verificar estructura
            product = response.data
            self.assertIn('id', product)
            self.assertIn('unit_price', product)
            self.assertIn('currency', product)
            self.assertIn('product_type', product)
            self.assertIn('product', product)
            
            # Verificar tipo correcto
            self.assertEqual(product['product_type'], expected_type)
            self.assertEqual(product['id'], metadata_id)
            
            print(f"  Tipo verificado: {product['product_type']}")
            print(f"  Precio: {product['unit_price']}")
    
    def test_get_products_test_endpoint(self):
        """Test del endpoint de diagnóstico GET /products/test/"""
        print("\n=== Test: GET /products/test/ - Endpoint de diagnóstico ===")
        
        response = self.client.get('/api/products/test/')
        
        print(f"Status Code: {response.status_code}")
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar estructura de respuesta
        data = response.data
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'success')
        
        # Verificar estadísticas
        self.assertIn('total_active_products', data)
        self.assertIn('by_type', data)
        self.assertIn('available_products', data)
        self.assertIn('products_with_issues', data)
        
        print(f"Total productos activos: {data['total_active_products']}")
        print(f"Productos por tipo: {data['by_type']}")
        print(f"Productos disponibles: {data['available_products']}")
        print(f"Productos con problemas: {len(data['products_with_issues'])}")
        
        # Verificar que no hay productos con problemas
        self.assertEqual(len(data['products_with_issues']), 0)
    
    def test_serialize_product_metadata_function(self):
        """Test directo de la función de serialización"""
        print("\n=== Test: Función serialize_product_metadata ===")
        
        # Probar con cada tipo de producto
        test_cases = [
            (self.activity_metadata, "activity"),
            (self.flight_metadata, "flight"),
            (self.lodgment_metadata, "lodgment"),
            (self.transportation_metadata, "transportation")
        ]
        
        for metadata, expected_type in test_cases:
            print(f"\nProbando serialización de {expected_type}:")
            
            try:
                result = serialize_product_metadata(metadata)
                
                # Verificar estructura básica
                self.assertIn('id', result)
                self.assertIn('unit_price', result)
                self.assertIn('currency', result)
                self.assertIn('product_type', result)
                self.assertIn('product', result)
                
                # Verificar tipo correcto
                self.assertEqual(result['product_type'], expected_type)
                
                # Verificar que el precio es float
                self.assertIsInstance(result['unit_price'], float)
                
                # Verificar que el producto tiene datos
                product_data = result['product']
                self.assertIsNotNone(product_data)
                self.assertIn('id', product_data)
                
                print(f"  ✅ Serialización exitosa")
                print(f"  ID: {result['id']}")
                print(f"  Precio: {result['unit_price']}")
                
            except Exception as e:
                print(f"  ❌ Error en serialización: {str(e)}")
                self.fail(f"Error serializando {expected_type}: {str(e)}")
    
    def test_queryset_available_only(self):
        """Test del queryset available_only"""
        print("\n=== Test: Queryset available_only ===")
        
        try:
            # Obtener productos disponibles
            available_products = ProductsMetadata.objects.active().available_only()
            
            print(f"Total productos disponibles: {available_products.count()}")
            
            # Verificar que hay productos disponibles
            self.assertGreater(available_products.count(), 0)
            
            # Verificar que no hay errores en la consulta
            for product in available_products[:5]:  # Solo los primeros 5
                print(f"  Producto {product.id} ({product.product_type})")
                
                # Verificar que se puede acceder al contenido
                self.assertIsNotNone(product.content)
                
        except Exception as e:
            print(f"❌ Error en queryset: {str(e)}")
            self.fail(f"Error en queryset available_only: {str(e)}")
    
    def test_get_products_with_filters(self):
        """Test del endpoint con filtros"""
        print("\n=== Test: GET /products/ con filtros ===")
        
        # Test con filtro de tipo
        response = self.client.get('/api/products/', {'product_type': 'activity'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test con filtro de precio mínimo
        response = self.client.get('/api/products/', {'unit_price_min': 50})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test con filtro de precio máximo
        response = self.client.get('/api/products/', {'unit_price_max': 300})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        print("✅ Filtros funcionando correctamente")
    
    def test_get_products_edge_cases(self):
        """Test de casos edge y errores"""
        print("\n=== Test: Casos edge y errores ===")
        
        # Test con ID inexistente
        response = self.client.get('/api/products/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test con parámetros inválidos
        response = self.client.get('/api/products/', {'unit_price_min': 'invalid'})
        # Debería manejar el error graciosamente
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        
        print("✅ Casos edge manejados correctamente")
    
    def test_get_products_performance(self):
        """Test de rendimiento básico"""
        print("\n=== Test: Rendimiento ===")
        
        import time
        
        # Medir tiempo de respuesta
        start_time = time.time()
        response = self.client.get('/api/products/')
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"Tiempo de respuesta: {response_time:.3f} segundos")
        
        # Verificar que la respuesta es razonablemente rápida (< 2 segundos)
        self.assertLess(response_time, 2.0)
        
        # Verificar que la respuesta es exitosa
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        print("✅ Rendimiento aceptable")


if __name__ == '__main__':
    # Ejecutar tests específicos
    import django
    django.setup()
    
    # Crear instancia y ejecutar tests
    test_instance = TestGetProductsEndpoint()
    test_instance.setUp()
    
    print("🚀 Iniciando tests del endpoint GET de productos...")
    
    # Ejecutar tests en orden
    test_instance.test_get_products_list_success()
    test_instance.test_get_products_individual_success()
    test_instance.test_get_products_test_endpoint()
    test_instance.test_serialize_product_metadata_function()
    test_instance.test_queryset_available_only()
    test_instance.test_get_products_with_filters()
    test_instance.test_get_products_edge_cases()
    test_instance.test_get_products_performance()
    
    print("\n✅ Todos los tests completados exitosamente!") 