"""
Tests para verificar la liberación automática de stock cuando una orden se cancela.

Este test verifica que:
1. Cuando una orden cambia a estado CANCELLED, se libera automáticamente el stock
2. Cuando una orden cambia a estado REFUNDED, también se libera el stock
3. Si la orden ya estaba cancelada, no se libera stock duplicado
4. Se maneja correctamente el caso de productos no soportados
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from api.store.models import Cart, CartItem, Orders, OrderDetails
from api.store.services import services_cart as cart_srv
from api.store.services import services_orders as order_srv
from api.products.models import ProductsMetadata, Activity, ActivityAvailability
from api.products.services.stock_services import InsufficientStockError

User = get_user_model()


class TestOrderCancellationStockRelease(TestCase):
    """Tests para la liberación automática de stock en cancelación de órdenes."""

    def setUp(self):
        """Configuración inicial para los tests."""
        # Crear usuario
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        # Crear actividad y disponibilidad
        self.activity = Activity.objects.create(
            name="Test Activity",
            description="Test Description",
            price=Decimal("100.00"),
            currency="USD"
        )
        
        self.availability = ActivityAvailability.objects.create(
            activity=self.activity,
            date=timezone.now().date(),
            available_seats=10,
            reserved_seats=0,
            is_active=True
        )
        
        # Crear metadata del producto
        self.metadata = ProductsMetadata.objects.create(
            product_type="activity",
            product_id=self.activity.id,
            currency="USD",
            is_active=True
        )
        
        # Crear carrito
        self.cart = Cart.objects.create(
            client=self.user,
            status="OPEN",
            currency="USD"
        )

    def test_stock_released_when_order_cancelled(self):
        """Test: stock se libera cuando la orden pasa a CANCELLED."""
        # Añadir ítem al carrito usando helper
        cart_srv.add_item(
            cart=self.cart,
            metadata=self.metadata,
            availability_id=self.availability.id,
            qty=3,
            unit_price=Decimal("100.00")
        )
        
        # Hacer checkout para crear la orden
        order = cart_srv.checkout(self.cart, order_srv.create_order_from_cart)
        
        # Verificar que se reservó el stock
        self.availability.refresh_from_db()
        self.assertEqual(self.availability.reserved_seats, 3)
        
        # Cambiar estado a CANCELLED
        order.state = "Cancelled"
        order.save()
        
        # Verificar que se liberó el stock
        self.availability.refresh_from_db()
        self.assertEqual(self.availability.reserved_seats, 0)

    def test_stock_released_when_order_refunded(self):
        """Test: stock se libera cuando la orden pasa a REFUNDED."""
        # Añadir ítem al carrito usando helper
        cart_srv.add_item(
            cart=self.cart,
            metadata=self.metadata,
            availability_id=self.availability.id,
            qty=2,
            unit_price=Decimal("100.00")
        )
        
        # Hacer checkout para crear la orden
        order = cart_srv.checkout(self.cart, order_srv.create_order_from_cart)
        
        # Verificar que se reservó el stock
        self.availability.refresh_from_db()
        self.assertEqual(self.availability.reserved_seats, 2)
        
        # Cambiar estado a REFUNDED
        order.state = "Refunded"
        order.save()
        
        # Verificar que se liberó el stock
        self.availability.refresh_from_db()
        self.assertEqual(self.availability.reserved_seats, 0)

    def test_no_duplicate_stock_release(self):
        """Test: no se libera stock duplicado si la orden ya estaba cancelada."""
        # Añadir ítem al carrito usando helper
        cart_srv.add_item(
            cart=self.cart,
            metadata=self.metadata,
            availability_id=self.availability.id,
            qty=1,
            unit_price=Decimal("100.00")
        )
        
        # Hacer checkout para crear la orden
        order = cart_srv.checkout(self.cart, order_srv.create_order_from_cart)
        
        # Cambiar estado a CANCELLED (primera vez)
        order.state = "Cancelled"
        order.save()
        
        # Verificar que se liberó el stock
        self.availability.refresh_from_db()
        self.assertEqual(self.availability.reserved_seats, 0)
        
        # Cambiar estado a CANCELLED nuevamente (no debería liberar más stock)
        order.save()
        
        # Verificar que el stock sigue en 0
        self.availability.refresh_from_db()
        self.assertEqual(self.availability.reserved_seats, 0)

    def test_multiple_order_details_stock_release(self):
        """Test: se libera stock de múltiples detalles de orden."""
        # Crear segunda disponibilidad
        availability2 = ActivityAvailability.objects.create(
            activity=self.activity,
            date=timezone.now().date() + timezone.timedelta(days=1),
            available_seats=5,
            reserved_seats=0,
            is_active=True
        )
        
        # Añadir dos ítems al carrito usando helper
        cart_srv.add_item(
            cart=self.cart,
            metadata=self.metadata,
            availability_id=self.availability.id,
            qty=2,
            unit_price=Decimal("100.00")
        )
        
        cart_srv.add_item(
            cart=self.cart,
            metadata=self.metadata,
            availability_id=availability2.id,
            qty=3,
            unit_price=Decimal("100.00")
        )
        
        # Hacer checkout para crear la orden
        order = cart_srv.checkout(self.cart, order_srv.create_order_from_cart)
        
        # Verificar que se reservó el stock en ambas disponibilidades
        self.availability.refresh_from_db()
        availability2.refresh_from_db()
        self.assertEqual(self.availability.reserved_seats, 2)
        self.assertEqual(availability2.reserved_seats, 3)
        
        # Cambiar estado a CANCELLED
        order.state = "Cancelled"
        order.save()
        
        # Verificar que se liberó el stock en ambas disponibilidades
        self.availability.refresh_from_db()
        availability2.refresh_from_db()
        self.assertEqual(self.availability.reserved_seats, 0)
        self.assertEqual(availability2.reserved_seats, 0)

    def test_unsupported_product_type_ignored(self):
        """Test: productos no soportados se ignoran sin error."""
        # Crear metadata de producto no soportado
        unsupported_metadata = ProductsMetadata.objects.create(
            product_type="unsupported",
            product_id=999,
            currency="USD",
            is_active=True
        )
        # Añadir ítem al carrito usando helper
        cart_srv.add_item(
            cart=self.cart,
            metadata=unsupported_metadata,
            availability_id=999,
            qty=1,
            unit_price=Decimal("100.00")
        )
        # Hacer checkout para crear la orden
        order = cart_srv.checkout(self.cart, order_srv.create_order_from_cart)
        # Cambiar estado a CANCELLED
        order.state = "Cancelled"
        order.save()
        # No debe lanzar excepción 