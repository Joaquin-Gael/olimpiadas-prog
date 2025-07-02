#!/usr/bin/env python3
"""
Script de pruebas rápidas para verificar endpoints básicos
"""

import requests
import json
from datetime import date, timedelta

def test_endpoint(url, method="GET", data=None, expected_status=200):
    """Función helper para probar endpoints"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == expected_status:
            print(f"✅ {method} {url} - Status: {response.status_code}")
            return True, response.json() if response.content else None
        else:
            print(f"❌ {method} {url} - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False, response.text
    except Exception as e:
        print(f"❌ {method} {url} - Exception: {str(e)}")
        return False, str(e)

def main():
    """Pruebas rápidas de endpoints"""
    base_url = "http://localhost:8000"
    
    print("🚀 PRUEBAS RÁPIDAS DE ENDPOINTS")
    print("=" * 40)
    
    # Verificar que el servidor esté corriendo
    success, _ = test_endpoint(f"{base_url}/")
    if not success:
        print("❌ No se pudo conectar al servidor")
        print("   Ejecuta: python manage.py runserver")
        return
    
    print("\n📋 Probando endpoints básicos...")
    
    # 1. Listar productos (debería funcionar siempre)
    success, data = test_endpoint(f"{base_url}/products/productos/")
    if success and data:
        print(f"   📊 Productos encontrados: {len(data)}")
    
    # 2. Listar proveedores
    success, data = test_endpoint(f"{base_url}/suppliers/")
    if success and data:
        print(f"   📊 Proveedores encontrados: {len(data)}")
    
    # 3. Listar paquetes
    success, data = test_endpoint(f"{base_url}/package/paquetes/")
    if success and data:
        print(f"   📊 Paquetes encontrados: {len(data)}")
    
    print("\n🔍 Probando filtros de productos...")
    
    # 4. Filtrar por tipo
    success, data = test_endpoint(f"{base_url}/products/productos/?tipo=activity")
    if success and data:
        print(f"   📊 Actividades encontradas: {len(data)}")
    
    # 5. Filtrar por precio
    success, data = test_endpoint(f"{base_url}/products/productos/?precio_max=1000")
    if success and data:
        print(f"   📊 Productos con precio <= 1000: {len(data)}")
    
    # 6. Ordenar por precio
    success, data = test_endpoint(f"{base_url}/products/productos/?ordering=precio")
    if success and data:
        print(f"   📊 Productos ordenados por precio: {len(data)}")
    
    print("\n📝 Probando creación de datos...")
    
    # 7. Crear un proveedor de prueba
    supplier_data = {
        "first_name": "Test",
        "last_name": "User",
        "organization_name": "Test Organization",
        "description": "Organización de prueba",
        "street": "Test Street",
        "street_number": 123,
        "city": "Test City",
        "country": "Test Country",
        "email": "test@test.com",
        "telephone": "+1234567890",
        "website": "https://test.com"
    }
    
    success, data = test_endpoint(f"{base_url}/suppliers/", "POST", supplier_data)
    if success:
        print(f"   ✅ Proveedor creado con ID: {data.get('id', 'N/A')}")
        supplier_id = data.get('id')
    else:
        print("   ❌ No se pudo crear proveedor")
        supplier_id = None
    
    print("\n📊 RESUMEN")
    print("=" * 40)
    print("✅ Endpoints básicos probados")
    print("✅ Filtros de productos probados")
    if supplier_id:
        print("✅ Creación de datos probada")
    else:
        print("⚠️  Creación de datos falló")
    
    print("\n💡 Para pruebas más completas ejecuta:")
    print("   python test_endpoints_produccion.py")

if __name__ == "__main__":
    main() 