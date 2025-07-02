"""
Tests para verificar el re-chequeo de stock durante el checkout.

Este test verifica que:
1. Si una Availability se cancela después de añadir al carrito, el checkout falla
2. Si hay stock insuficiente, se devuelve 409 Conflict
3. El carrito permanece en estado OPEN si falla el checkout
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from api.store.models import Cart, CartItem
from api.store.services import services_cart as cart_srv
from api.store.services import services_orders as order_srv
from api.products.models import ProductsMetadata, Activity, ActivityAvailability
from api.products.services.stock_services import InsufficientStockError

User = get_user_model()


class TestCheckoutStockValidation(TestCase):
    """Tests para el re-chequeo de stock en checkout."""

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

    def test_checkout_success_with_valid_stock(self):
        """Test: checkout exitoso cuando hay stock válido."""
        # Añadir ítem al carrito
        item = cart_srv.add_item(
            cart=self.cart,
            metadata=self.metadata,
            availability_id=self.availability.id,
            qty=2,
            unit_price=Decimal("100.00")
        )
        
        # Verificar que el ítem se añadió
        self.assertEqual(self.cart.items.count(), 1)
        self.assertEqual(item.qty, 2)
        
        # Hacer checkout
        order = cart_srv.checkout(self.cart, order_srv.create_order_from_cart)
        
        # Verificar que se creó la orden
        self.assertIsNotNone(order)
        self.assertEqual(order.client, self.user)
        self.assertEqual(float(order.total), 200.00)
        
        # Verificar que el carrito cambió a ORDERED
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, "ORDERED")

    def test_checkout_fails_when_availability_cancelled(self):
        """Test: checkout falla cuando la disponibilidad se cancela."""
        # Añadir ítem al carrito
        cart_srv.add_item(
            cart=self.cart,
            metadata=self.metadata,
            availability_id=self.availability.id,
            qty=2,
            unit_price=Decimal("100.00")
        )
        
        # Simular que un admin cancela la disponibilidad
        self.availability.is_active = False
        self.availability.save()
        
        # Intentar checkout - debe fallar
        with self.assertRaises(InsufficientStockError):
            cart_srv.checkout(self.cart, order_srv.create_order_from_cart)
        
        # Verificar que el carrito sigue OPEN
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, "OPEN")

    def test_checkout_fails_when_insufficient_stock(self):
        """Test: checkout falla cuando no hay stock suficiente."""
        # Añadir ítem al carrito
        cart_srv.add_item(
            cart=self.cart,
            metadata=self.metadata,
            availability_id=self.availability.id,
            qty=5,
            unit_price=Decimal("100.00")
        )
        
        # Simular que se agotó el stock (otro usuario reservó todo)
        self.availability.available_seats = 0
        self.availability.save()
        
        # Intentar checkout - debe fallar
        with self.assertRaises(InsufficientStockError):
            cart_srv.checkout(self.cart, order_srv.create_order_from_cart)
        
        # Verificar que el carrito sigue OPEN
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, "OPEN")

    def test_checkout_fails_when_availability_deleted(self):
        """Test: checkout falla cuando la disponibilidad se elimina."""
        # Añadir ítem al carrito
        cart_srv.add_item(
            cart=self.cart,
            metadata=self.metadata,
            availability_id=self.availability.id,
            qty=2,
            unit_price=Decimal("100.00")
        )
        
        # Simular que se elimina la disponibilidad
        self.availability.delete()
        
        # Intentar checkout - debe fallar
        with self.assertRaises(InsufficientStockError):
            cart_srv.checkout(self.cart, order_srv.create_order_from_cart)
        
        # Verificar que el carrito sigue OPEN
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, "OPEN")

    def test_checkout_with_multiple_items_partial_failure(self):
        """Test: checkout falla si uno de varios ítems no tiene stock."""
        # Crear segunda disponibilidad
        availability2 = ActivityAvailability.objects.create(
            activity=self.activity,
            date=timezone.now().date() + timezone.timedelta(days=1),
            available_seats=5,
            reserved_seats=0,
            is_active=True
        )
        
        # Añadir dos ítems al carrito
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
        
        # Verificar que hay dos ítems
        self.assertEqual(self.cart.items.count(), 2)
        
        # Cancelar una disponibilidad
        availability2.is_active = False
        availability2.save()
        
        # Intentar checkout - debe fallar
        with self.assertRaises(InsufficientStockError):
            cart_srv.checkout(self.cart, order_srv.create_order_from_cart)
        
        # Verificar que el carrito sigue OPEN
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, "OPEN") 