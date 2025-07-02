#!/usr/bin/env python3
"""
Script de pruebas para verificar endpoints en condiciones similares a producción
"""

import os
import sys
import django
import requests
import json
from datetime import date, timedelta
from typing import Dict, Any

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

from django.test import TestCase
from django.urls import reverse
from api.products.models import (
    Suppliers, Location, Activities, Flights, Lodgment, Transportation,
    ProductsMetadata, ActivityAvailability
)
from django.contrib.contenttypes.models import ContentType

class EndpointTester:
    """Clase para probar endpoints de manera similar a producción"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_data = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log con formato"""
        print(f"[{level}] {message}")
    
    def create_test_data(self):
        """Crear datos de prueba más realistas"""
        self.log("Creando datos de prueba...")
        
        # Crear ubicaciones realistas
        locations = []
        for i in range(3):
            location = Location.objects.create(
                country="Argentina",
                state=f"Provincia {i+1}",
                city=f"Ciudad {i+1}"
            )
            locations.append(location)
        
        # Crear proveedores realistas
        suppliers = []
        supplier_data = [
            {
                "first_name": "María",
                "last_name": "González",
                "organization_name": "Turismo Aventura SA",
                "description": "Especialistas en deportes extremos y ecoturismo",
                "street": "Av. Libertador",
                "street_number": 1234,
                "city": "Buenos Aires",
                "country": "Argentina",
                "email": "info@turismoaventura.com",
                "telephone": "+54 11 1234-5678",
                "website": "https://turismoaventura.com"
            },
            {
                "first_name": "Carlos",
                "last_name": "Rodríguez",
                "organization_name": "Hoteles Premium",
                "description": "Cadena de hoteles de lujo en todo el país",
                "street": "Calle Florida",
                "street_number": 567,
                "city": "Buenos Aires",
                "country": "Argentina",
                "email": "reservas@hotelespremium.com",
                "telephone": "+54 11 9876-5432",
                "website": "https://hotelespremium.com"
            }
        ]
        
        for data in supplier_data:
            supplier = Suppliers.objects.create(**data)
            suppliers.append(supplier)
        
        self.test_data = {
            "locations": locations,
            "suppliers": suppliers
        }
        
        self.log(f"Creados {len(locations)} locations y {len(suppliers)} suppliers")
    
    def test_create_activity(self) -> Dict[str, Any]:
        """Probar creación de actividad"""
        self.log("Probando creación de actividad...")
        
        payload = {
            "tipo_producto": "activity",
            "precio_unitario": 150.0,
            "supplier_id": self.test_data["suppliers"][0].id,
            "producto": {
                "name": "Trekking en la Montaña",
                "description": "Excursión guiada por senderos de montaña con vistas panorámicas",
                "location_id": self.test_data["locations"][0].id,
                "date": str(date.today() + timedelta(days=15)),
                "start_time": "08:00:00",
                "duration_hours": 6,
                "include_guide": True,
                "maximum_spaces": 12,
                "difficulty_level": "Medium",
                "language": "Español",
                "available_slots": 12
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/products/productos/crear/",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Actividad creada exitosamente: {data['producto']['name']}")
                return {"success": True, "data": data, "id": data["id"]}
            else:
                self.log(f"❌ Error creando actividad: {response.status_code} - {response.text}", "ERROR")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.log(f"❌ Excepción creando actividad: {str(e)}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def test_create_activity_complete(self) -> Dict[str, Any]:
        """Probar creación de actividad completa con disponibilidades"""
        self.log("Probando creación de actividad completa...")
        
        payload = {
            "name": "Kayak en el Lago",
            "description": "Paseo guiado por aguas tranquilas del lago",
            "location_id": self.test_data["locations"][1].id,
            "date": str(date.today() + timedelta(days=20)),
            "start_time": "10:00:00",
            "duration_hours": 3,
            "include_guide": True,
            "maximum_spaces": 8,
            "difficulty_level": "Easy",
            "language": "Español",
            "available_slots": 8,
            "supplier_id": self.test_data["suppliers"][0].id,
            "precio_unitario": 120.0,
            "currency": "USD",
            "availabilities": [
                {
                    "event_date": str(date.today() + timedelta(days=20)),
                    "start_time": "10:00:00",
                    "total_seats": 8,
                    "reserved_seats": 0,
                    "price": 120.0,
                    "currency": "USD"
                },
                {
                    "event_date": str(date.today() + timedelta(days=21)),
                    "start_time": "10:00:00",
                    "total_seats": 8,
                    "reserved_seats": 2,
                    "price": 120.0,
                    "currency": "USD"
                }
            ]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/products/productos/actividad-completa/",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Actividad completa creada: {data['producto']['name']}")
                return {"success": True, "data": data, "id": data["id"]}
            else:
                self.log(f"❌ Error creando actividad completa: {response.status_code} - {response.text}", "ERROR")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.log(f"❌ Excepción creando actividad completa: {str(e)}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def test_list_products(self) -> Dict[str, Any]:
        """Probar listado de productos con filtros"""
        self.log("Probando listado de productos...")
        
        # Probar diferentes filtros
        test_filters = [
            {"tipo": "activity"},
            {"precio_max": 200},
            {"destino_id": self.test_data["locations"][0].id},
            {"ordering": "precio"},
            {"tipo": "activity", "precio_max": 200, "ordering": "precio"}
        ]
        
        results = []
        for i, filters in enumerate(test_filters):
            try:
                response = self.session.get(
                    f"{self.base_url}/products/productos/",
                    params=filters,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✅ Filtro {i+1} exitoso: {len(data)} productos encontrados")
                    results.append({"success": True, "filters": filters, "count": len(data)})
                else:
                    self.log(f"❌ Error en filtro {i+1}: {response.status_code}", "ERROR")
                    results.append({"success": False, "filters": filters, "error": response.text})
                    
            except Exception as e:
                self.log(f"❌ Excepción en filtro {i+1}: {str(e)}", "ERROR")
                results.append({"success": False, "filters": filters, "error": str(e)})
        
        return {"success": True, "results": results}
    
    def test_get_product_by_id(self, product_id: int) -> Dict[str, Any]:
        """Probar obtención de producto por ID"""
        self.log(f"Probando obtención de producto ID: {product_id}")
        
        try:
            response = self.session.get(
                f"{self.base_url}/products/productos/{product_id}/",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Producto obtenido: {data['producto']['name']}")
                return {"success": True, "data": data}
            else:
                self.log(f"❌ Error obteniendo producto: {response.status_code}", "ERROR")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.log(f"❌ Excepción obteniendo producto: {str(e)}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def test_get_activity_availability(self, product_id: int) -> Dict[str, Any]:
        """Probar obtención de disponibilidades de actividad"""
        self.log(f"Probando disponibilidades de actividad ID: {product_id}")
        
        try:
            response = self.session.get(
                f"{self.base_url}/products/productos/{product_id}/availability/",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Disponibilidades obtenidas: {len(data)} registros")
                return {"success": True, "data": data}
            else:
                self.log(f"❌ Error obteniendo disponibilidades: {response.status_code}", "ERROR")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.log(f"❌ Excepción obteniendo disponibilidades: {str(e)}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def test_suppliers_endpoints(self) -> Dict[str, Any]:
        """Probar endpoints de proveedores"""
        self.log("Probando endpoints de proveedores...")
        
        try:
            # Listar proveedores
            response = self.session.get(
                f"{self.base_url}/suppliers/",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Proveedores listados: {len(data)} encontrados")
                return {"success": True, "list_count": len(data)}
            else:
                self.log(f"❌ Error listando proveedores: {response.status_code}", "ERROR")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.log(f"❌ Excepción en proveedores: {str(e)}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        self.log("🚀 Iniciando pruebas de endpoints...")
        
        # Crear datos de prueba
        self.create_test_data()
        
        results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        # Test 1: Crear actividad simple
        results["total_tests"] += 1
        result = self.test_create_activity()
        if result["success"]:
            results["passed"] += 1
            activity_id = result["id"]
        else:
            results["failed"] += 1
            activity_id = None
        results["details"].append({"test": "create_activity", "result": result})
        
        # Test 2: Crear actividad completa
        results["total_tests"] += 1
        result = self.test_create_activity_complete()
        if result["success"]:
            results["passed"] += 1
            activity_complete_id = result["id"]
        else:
            results["failed"] += 1
            activity_complete_id = None
        results["details"].append({"test": "create_activity_complete", "result": result})
        
        # Test 3: Listar productos
        results["total_tests"] += 1
        result = self.test_list_products()
        if result["success"]:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({"test": "list_products", "result": result})
        
        # Test 4: Obtener producto por ID (si se creó exitosamente)
        if activity_id:
            results["total_tests"] += 1
            result = self.test_get_product_by_id(activity_id)
            if result["success"]:
                results["passed"] += 1
            else:
                results["failed"] += 1
            results["details"].append({"test": "get_product_by_id", "result": result})
        
        # Test 5: Obtener disponibilidades (si se creó exitosamente)
        if activity_complete_id:
            results["total_tests"] += 1
            result = self.test_get_activity_availability(activity_complete_id)
            if result["success"]:
                results["passed"] += 1
            else:
                results["failed"] += 1
            results["details"].append({"test": "get_activity_availability", "result": result})
        
        # Test 6: Endpoints de proveedores
        results["total_tests"] += 1
        result = self.test_suppliers_endpoints()
        if result["success"]:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({"test": "suppliers_endpoints", "result": result})
        
        # Mostrar resumen
        self.log("=" * 50)
        self.log("📊 RESUMEN DE PRUEBAS")
        self.log("=" * 50)
        self.log(f"Total de pruebas: {results['total_tests']}")
        self.log(f"✅ Exitosas: {results['passed']}")
        self.log(f"❌ Fallidas: {results['failed']}")
        self.log(f"📈 Tasa de éxito: {(results['passed']/results['total_tests']*100):.1f}%")
        
        if results["failed"] > 0:
            self.log("\n🔍 DETALLES DE FALLOS:")
            for detail in results["details"]:
                if not detail["result"]["success"]:
                    self.log(f"  - {detail['test']}: {detail['result'].get('error', 'Error desconocido')}")
        
        return results

def main():
    """Función principal"""
    print("🧪 TESTER DE ENDPOINTS - SIMULACIÓN DE PRODUCCIÓN")
    print("=" * 60)
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print("✅ Servidor detectado en http://localhost:8000")
    except:
        print("❌ No se pudo conectar al servidor en http://localhost:8000")
        print("   Asegúrate de que el servidor Django esté corriendo:")
        print("   python manage.py runserver")
        return
    
    # Ejecutar pruebas
    tester = EndpointTester()
    results = tester.run_all_tests()
    
    # Guardar resultados en archivo
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Resultados guardados en: test_results.json")

if __name__ == "__main__":
    main() 