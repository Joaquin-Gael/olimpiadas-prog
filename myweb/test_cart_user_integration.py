#!/usr/bin/env python3
"""
Script de prueba para verificar la integración del carrito con el sistema de usuarios
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

from django.test import RequestFactory
from api.store.views_cart import get_cart, get_cart_with_user_info
from api.store.models import Cart, CartItem
from api.users.models import Users
from api.products.models import ProductsMetadata, Suppliers
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

def test_cart_user_integration():
    """Prueba la integración del carrito con el sistema de usuarios"""
    print("🔍 Probando integración carrito-usuario...")
    
    try:
        # 1. Verificar usuarios
        users = Users.objects.all()
        print(f"✅ Usuarios encontrados: {users.count()}")
        
        if users.count() == 0:
            print("❌ No hay usuarios en la base de datos")
            return
        
        user = users.first()
        print(f"👤 Usando usuario: {user.id} - {user.email}")
        print(f"   Nombre: {user.first_name} {user.last_name}")
        print(f"   Estado: {user.state}")
        print(f"   Activo: {user.is_active}")
        
        # 2. Verificar carritos existentes
        existing_carts = Cart.objects.filter(user=user)
        print(f"🛒 Carritos existentes: {existing_carts.count()}")
        
        # 3. Probar endpoint básico del carrito
        print("\n🚀 Probando endpoint GET /cart/...")
        factory = RequestFactory()
        request = factory.get('/cart/')
        request.user = user
        
        try:
            response = get_cart(request)
            print("✅ Endpoint GET /cart/ funcionando:")
            print(f"   - ID del carrito: {response.id}")
            print(f"   - User ID: {response.user_id}")
            print(f"   - Status: {response.status}")
            print(f"   - Items count: {response.items_cnt}")
            print(f"   - Total: {response.total}")
            print(f"   - Currency: {response.currency}")
            
            if response.user_info:
                print(f"   - User info: {response.user_info.first_name} {response.user_info.last_name}")
            
        except Exception as e:
            print(f"❌ Error en GET /cart/: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 4. Probar endpoint con información completa del usuario
        print("\n🚀 Probando endpoint GET /cart/user-info/...")
        try:
            response = get_cart_with_user_info(request)
            print("✅ Endpoint GET /cart/user-info/ funcionando:")
            print(f"   - User ID: {response['user']['id']}")
            print(f"   - User name: {response['user']['first_name']} {response['user']['last_name']}")
            print(f"   - User email: {response['user']['email']}")
            print(f"   - Cart ID: {response['cart']['id']}")
            print(f"   - Cart status: {response['cart']['status']}")
            
        except Exception as e:
            print(f"❌ Error en GET /cart/user-info/: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 5. Verificar que el carrito se creó correctamente
        cart = Cart.objects.filter(user=user, status="OPEN").first()
        if cart:
            print(f"\n✅ Carrito verificado en BD:")
            print(f"   - ID: {cart.id}")
            print(f"   - User: {cart.user.email}")
            print(f"   - Status: {cart.status}")
            print(f"   - Items: {cart.items_cnt}")
            print(f"   - Total: {cart.total}")
            
            # Verificar items
            items = cart.items.all()
            print(f"   - Items en BD: {items.count()}")
            
        else:
            print("❌ No se encontró carrito en la base de datos")
        
        print("\n🎉 Prueba de integración completada")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cart_user_integration() 