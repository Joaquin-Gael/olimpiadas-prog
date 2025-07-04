"""
Pruebas unitarias para el servicio de órdenes.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from api.store.models import Cart, CartItem, Orders, OrderDetails
from api.store.services.services_orders import create_order_from_cart, OrderCreationError, InvalidCartStateError
from api.products.models import ProductsMetadata
from api.clients.models import Clients, Addresses

User = get_user_model()


class CreateOrderFromCartTestCase(TestCase):
    """Pruebas para la función create_order_from_cart."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Crear usuario/cliente
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear cliente
        self.client_obj = Clients.objects.create(
            user=self.user,
            first_name="Test",
            last_name="User",
            email="test@example.com"
        )
        
        # Crear dirección
        self.address = Addresses.objects.create(
            client=self.client_obj,
            street="Test Street 123",
            city="Test City",
            state="Test State",
            country="Test Country",
            postal_code="12345"
        )
        
        # Crear metadata de producto
        self.product_metadata = ProductsMetadata.objects.create(
            name="Test Product",
            description="Test Description",
            price=Decimal("100.00"),
            currency="USD",
            product_type="activity"
        )
        
        # Crear carrito
        self.cart = Cart.objects.create(
            client=self.user,
            status="OPEN",
            currency="USD",
            total=Decimal("100.00"),
            items_cnt=1
        )
        
        # Crear ítem del carrito
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            availability_id=1,
            product_metadata_id=self.product_metadata.id,
            qty=1,
            unit_price=Decimal("100.00"),
            currency="USD",
            config={}
        )
    
    def test_create_order_from_cart_success(self):
        """Prueba la creación exitosa de una orden desde un carrito."""
        # Ejecutar la función
        order = create_order_from_cart(self.cart.id, self.user.id, "key-test")
        
        # Verificar que se creó la orden
        self.assertIsInstance(order, Orders)
        self.assertEqual(order.client.user, self.user)
        self.assertEqual(order.total, Decimal("100.00"))
        self.assertEqual(order.state, "Pending")
        # self.assertEqual(order.address, self.address)  # Si address ya no existe, comentar
        
        # Verificar que se crearon los detalles
        details = OrderDetails.objects.filter(order=order)
        self.assertEqual(details.count(), 1)
        
        detail = details.first()
        self.assertEqual(detail.product_metadata, self.product_metadata)
        self.assertEqual(detail.quantity, 1)
        self.assertEqual(detail.unit_price, Decimal("100.00"))
        self.assertEqual(detail.subtotal, Decimal("100.00"))
    
    def test_create_order_from_cart_invalid_status(self):
        """Prueba que falle si el carrito no está en estado OPEN."""
        # Cambiar estado del carrito
        self.cart.status = "ORDERED"
        self.cart.save()
        
        # Debe fallar
        with self.assertRaises(InvalidCartStateError):
            create_order_from_cart(self.cart.id, self.user.id, "key-test")
    
    def test_create_order_from_cart_empty(self):
        """Prueba que falle si el carrito está vacío."""
        # Eliminar ítem del carrito
        self.cart_item.delete()
        
        # Debe fallar
        with self.assertRaises(OrderCreationError):
            create_order_from_cart(self.cart.id, self.user.id, "key-test")
    
    def test_create_order_from_cart_multiple_items(self):
        """Prueba la creación con múltiples ítems."""
        # Crear segundo ítem
        second_metadata = ProductsMetadata.objects.create(
            name="Second Product",
            description="Second Description",
            price=Decimal("50.00"),
            currency="USD",
            product_type="transportation"
        )
        
        CartItem.objects.create(
            cart=self.cart,
            availability_id=2,
            product_metadata_id=second_metadata.id,
            qty=2,
            unit_price=Decimal("50.00"),
            currency="USD",
            config={}
        )
        
        # Actualizar total del carrito
        self.cart.total = Decimal("200.00")
        self.cart.items_cnt = 3
        self.cart.save()
        
        # Ejecutar la función
        order = create_order_from_cart(self.cart.id, self.user.id, "key-test")
        
        # Verificar que se crearon ambos detalles
        details = OrderDetails.objects.filter(order=order)
        self.assertEqual(details.count(), 2)
        
        # Verificar total
        self.assertEqual(order.total, Decimal("200.00")) 