#!/usr/bin/env python3
"""
Script de diagnóstico simple para el endpoint del carrito
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

from django.test import RequestFactory
from api.store.views_cart import get_cart
from api.store.models import Cart, CartItem
from api.users.models import Users
from api.products.models import ProductsMetadata

def test_cart_basic():
    """Prueba básica del carrito"""
    print("🔍 Diagnóstico básico del carrito...")
    
    try:
        # 1. Verificar usuarios
        users = Users.objects.all()
        print(f"✅ Usuarios: {users.count()}")
        
        if users.count() == 0:
            print("❌ No hay usuarios")
            return
        
        user = users.first()
        print(f"👤 Usuario: {user.id} - {user.email}")
        
        # 2. Verificar carritos
        carts = Cart.objects.filter(user=user)
        print(f"🛒 Carritos: {carts.count()}")
        
        # 3. Crear o obtener carrito
        cart, created = Cart.objects.get_or_create(
            user=user,
            status="OPEN",
            defaults={"currency": "USD", "total": Decimal("0.00"), "items_cnt": 0}
        )
        
        print(f"✅ Carrito: {cart.id} (creado: {created})")
        print(f"   Status: {cart.status}")
        print(f"   Items: {cart.items_cnt}")
        print(f"   Total: {cart.total}")
        print(f"   Currency: {cart.currency}")
        
        # 4. Verificar items
        items = cart.items.all()
        print(f"📝 Items en carrito: {items.count()}")
        
        # 5. Probar endpoint
        print("🚀 Probando endpoint...")
        factory = RequestFactory()
        request = factory.get('/cart/')
        request.user = user
        
        try:
            response = get_cart(request)
            print("✅ Endpoint funcionó")
            print(f"   Tipo respuesta: {type(response)}")
            
            # Intentar acceder a los campos
            if hasattr(response, 'id'):
                print(f"   ID: {response.id}")
            if hasattr(response, 'status'):
                print(f"   Status: {response.status}")
            if hasattr(response, 'items_cnt'):
                print(f"   Items count: {response.items_cnt}")
            if hasattr(response, 'total'):
                print(f"   Total: {response.total}")
            if hasattr(response, 'currency'):
                print(f"   Currency: {response.currency}")
            if hasattr(response, 'items'):
                print(f"   Items: {len(response.items)}")
                
        except Exception as e:
            print(f"❌ Error en endpoint: {str(e)}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        import traceback
        traceback.print_exc()

def test_cart_serialization():
    """Prueba la serialización específicamente"""
    print("\n🔍 Probando serialización...")
    
    try:
        cart = Cart.objects.filter(status="OPEN").first()
        if not cart:
            print("❌ No hay carritos abiertos")
            return
        
        print(f"🛒 Carrito: {cart.id}")
        
        # Probar serialización directa
        from api.store.schemas import CartOut
        
        try:
            cart_out = CartOut.from_orm(cart)
            print("✅ Serialización exitosa")
            print(f"   ID: {cart_out.id}")
            print(f"   Status: {cart_out.status}")
            print(f"   Items count: {cart_out.items_cnt}")
            print(f"   Total: {cart_out.total}")
            print(f"   Currency: {cart_out.currency}")
            print(f"   Items: {len(cart_out.items)}")
            
        except Exception as e:
            print(f"❌ Error en serialización: {str(e)}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando diagnóstico del carrito...")
    test_cart_basic()
    test_cart_serialization()
    print("\n🏁 Fin del diagnóstico") 