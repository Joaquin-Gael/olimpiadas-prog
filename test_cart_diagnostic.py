#!/usr/bin/env python3
"""
Script de diagnóstico para el endpoint del carrito
"""
import os
import sys
import django
from decimal import Decimal

# Agregar el directorio myweb al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'myweb'))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from api.store.views_cart import get_cart
from api.store.models import Cart, CartItem
from api.users.models import Users
from api.products.models import ProductsMetadata
from api.core.auth import SyncJWTBearer

User = get_user_model()

def test_cart_endpoint():
    """Prueba el endpoint del carrito paso a paso"""
    print("🔍 Iniciando diagnóstico del carrito...")
    
    try:
        # 1. Verificar que hay usuarios en la base de datos
        users = Users.objects.all()
        print(f"✅ Usuarios encontrados: {users.count()}")
        
        if users.count() == 0:
            print("❌ No hay usuarios en la base de datos")
            return
        
        # Usar el primer usuario disponible
        user = users.first()
        print(f"👤 Usando usuario: {user.id} - {user.email}")
        
        # 2. Verificar carritos existentes
        existing_carts = Cart.objects.filter(user=user)
        print(f"🛒 Carritos existentes para el usuario: {existing_carts.count()}")
        
        for cart in existing_carts:
            print(f"   - Cart {cart.id}: status={cart.status}, items={cart.items_cnt}, total={cart.total}")
        
        # 3. Crear un carrito de prueba si no existe
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
            print(f"✅ Carrito creado: {cart.id}")
        else:
            print(f"✅ Usando carrito existente: {cart.id}")
        
        # 4. Verificar productos disponibles
        products = ProductsMetadata.objects.active()
        print(f"📦 Productos activos disponibles: {products.count()}")
        
        # 5. Simular una petición HTTP
        factory = RequestFactory()
        request = factory.get('/cart/')
        request.user = user
        
        # 6. Llamar al endpoint
        print("🚀 Llamando al endpoint get_cart...")
        response = get_cart(request)
        
        print("✅ Respuesta del endpoint:")
        print(f"   - Tipo de respuesta: {type(response)}")
        print(f"   - Contenido: {response}")
        
        # 7. Verificar la estructura de la respuesta
        if hasattr(response, 'dict'):
            response_dict = response.dict()
            print("📋 Estructura de la respuesta:")
            for key, value in response_dict.items():
                print(f"   - {key}: {value} (tipo: {type(value)})")
        
        # 8. Verificar el carrito en la base de datos después de la llamada
        cart.refresh_from_db()
        print(f"🔄 Carrito después de la llamada:")
        print(f"   - ID: {cart.id}")
        print(f"   - Status: {cart.status}")
        print(f"   - Items count: {cart.items_cnt}")
        print(f"   - Total: {cart.total}")
        print(f"   - Currency: {cart.currency}")
        print(f"   - Updated at: {cart.updated_at}")
        
        # 9. Verificar items del carrito
        items = cart.items.all()
        print(f"📝 Items en el carrito: {items.count()}")
        
        for item in items:
            print(f"   - Item {item.id}: qty={item.qty}, price={item.unit_price}, currency={item.currency}")
        
        print("✅ Diagnóstico completado exitosamente")
        
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {str(e)}")
        import traceback
        traceback.print_exc()

def test_cart_serialization():
    """Prueba la serialización del carrito específicamente"""
    print("\n🔍 Probando serialización del carrito...")
    
    try:
        # Obtener un carrito
        cart = Cart.objects.filter(status="OPEN").first()
        if not cart:
            print("❌ No hay carritos abiertos para probar")
            return
        
        print(f"🛒 Probando con carrito: {cart.id}")
        
        # Importar el schema
        from api.store.schemas import CartOut
        
        # Intentar serializar
        print("📝 Intentando serializar con CartOut.from_orm...")
        cart_out = CartOut.from_orm(cart)
        
        print("✅ Serialización exitosa:")
        print(f"   - ID: {cart_out.id}")
        print(f"   - Status: {cart_out.status}")
        print(f"   - Items count: {cart_out.items_cnt}")
        print(f"   - Total: {cart_out.total}")
        print(f"   - Currency: {cart_out.currency}")
        print(f"   - Updated at: {cart_out.updated_at}")
        print(f"   - Items: {len(cart_out.items)}")
        
        # Verificar cada item
        for i, item in enumerate(cart_out.items):
            print(f"     Item {i+1}: id={item.id}, qty={item.qty}, price={item.unit_price}")
        
    except Exception as e:
        print(f"❌ Error en serialización: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Iniciando diagnóstico completo del carrito...")
    test_cart_endpoint()
    test_cart_serialization()
    print("\n🏁 Diagnóstico completado") 