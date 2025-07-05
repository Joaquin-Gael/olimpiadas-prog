"""
Tests básicos y progresivos para el flujo de órdenes.
Empezamos con componentes simples y vamos expandiendo.
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from api.users.models import Users
from api.store.models import Cart, CartItem, Orders, OrderDetails, OrderState, CartStatus
from api.products.models import Packages, ProductsMetadata, ComponentPackages, Suppliers
from api.store.services.services_orders import create_order_from_cart, OrderService


class OrderBasicCreationTestCase(TestCase):
    """
    Tests básicos para la creación de órdenes.
    Paso 1: Validar que podemos crear órdenes simples.
    """
    
    def setUp(self):
        """Configuración básica para todos los tests"""
        # Usuario básico
        self.user = Users.objects.create_user(
            email='testuser@example.com', 
            password='1234', 
            first_name='Test', 
            last_name='User', 
            telephone='123456789'
        )
        
        # Paquete básico
        self.package = Packages.objects.create(
            name='Paquete Test', 
            description='Descripción del paquete', 
            final_price=Decimal('100.00')
        )
        
        # Proveedor básico
        self.supplier = Suppliers.objects.create(
            first_name='Proveedor',
            last_name='Test',
            organization_name='Organización Test',
            description='Descripción del proveedor',
            street='Calle Test',
            street_number=123,
            city='Ciudad Test',
            country='País Test',
            email='proveedor@test.com',
            telephone='123456789',
            website='https://test.com'
        )
        
        # ContentType para metadata
        self.content_type = ContentType.objects.create(
            app_label='products', 
            model='test_product'
        )
        
        # Metadata básica
        self.metadata = ProductsMetadata.objects.create(
            supplier=self.supplier,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30),
            content_type_id=self.content_type,
            object_id=1,
            unit_price=Decimal('50.00'),
            currency='USD',
            is_active=True
        )
        
        # Relación entre paquete y metadata
        self.component = ComponentPackages.objects.create(
            package=self.package,
            product_metadata=self.metadata,
            order=1
        )

    def test_1_create_basic_order(self):
        """
        Test 1: Crear una orden básica sin carrito.
        Valida que podemos crear órdenes directamente.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='test-key-1'
        )
        
        # Validaciones básicas
        self.assertIsNotNone(order.id)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.state, OrderState.PENDING)
        self.assertEqual(order.total, Decimal('100.00'))
        self.assertEqual(order.idempotency_key, 'test-key-1')
        self.assertIsNotNone(order.created_at)
        self.assertIsNotNone(order.updated_at)

    def test_2_create_order_with_details(self):
        """
        Test 2: Crear una orden con detalles.
        Valida que podemos agregar OrderDetails a una orden.
        """
        # Crear orden
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('50.00'),
            idempotency_key='test-key-2'
        )
        
        # Crear detalle de orden
        order_detail = OrderDetails.objects.create(
            order=order,
            product_metadata=self.metadata,
            package=self.package,
            availability_id=1,
            quantity=1,
            unit_price=Decimal('50.00'),
            subtotal=Decimal('50.00'),
            discount_applied=Decimal('0.00')
        )
        
        # Validaciones
        self.assertIsNotNone(order_detail.id)
        self.assertEqual(order_detail.order, order)
        self.assertEqual(order_detail.product_metadata, self.metadata)
        self.assertEqual(order_detail.package, self.package)
        self.assertEqual(order_detail.quantity, 1)
        self.assertEqual(order_detail.unit_price, Decimal('50.00'))
        self.assertEqual(order_detail.subtotal, Decimal('50.00'))

    def test_3_create_basic_cart(self):
        """
        Test 3: Crear un carrito básico.
        Valida que podemos crear carritos con items.
        """
        # Crear carrito
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('50.00'),
            items_cnt=1
        )
        
        # Crear item del carrito
        cart_item = CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('50.00'),
            currency='USD',
            config={}
        )
        
        # Validaciones
        self.assertIsNotNone(cart.id)
        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.status, CartStatus.OPEN)
        self.assertEqual(cart.total, Decimal('50.00'))
        self.assertEqual(cart.items_cnt, 1)
        
        self.assertIsNotNone(cart_item.id)
        self.assertEqual(cart_item.cart, cart)
        self.assertEqual(cart_item.product_metadata_id, self.metadata.id)
        self.assertEqual(cart_item.qty, 1)
        self.assertEqual(cart_item.unit_price, Decimal('50.00'))

    def test_4_order_service_get_order(self):
        """
        Test 4: Probar OrderService.get_order_by_id.
        Valida que el servicio puede recuperar órdenes.
        """
        # Crear orden
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='test-key-4'
        )
        
        # Usar el servicio para recuperar la orden
        retrieved_order = OrderService.get_order_by_id(order.id, self.user.id)
        
        # Validaciones
        self.assertIsNotNone(retrieved_order)
        self.assertEqual(retrieved_order.id, order.id)
        self.assertEqual(retrieved_order.user, self.user)
        self.assertEqual(retrieved_order.total, Decimal('100.00'))

    def test_5_order_service_get_nonexistent_order(self):
        """
        Test 5: Probar OrderService.get_order_by_id con orden inexistente.
        Valida que retorna None para órdenes que no existen.
        """
        # Intentar recuperar orden inexistente
        retrieved_order = OrderService.get_order_by_id(99999, self.user.id)
        
        # Debe retornar None
        self.assertIsNone(retrieved_order)

    def test_6_order_service_get_order_wrong_user(self):
        """
        Test 6: Probar OrderService.get_order_by_id con usuario incorrecto.
        Valida que no puede acceder a órdenes de otros usuarios.
        """
        # Crear otro usuario
        other_user = Users.objects.create_user(
            email='other@example.com',
            password='1234',
            first_name='Other',
            last_name='User',
            telephone='987654321'
        )
        
        # Crear orden para el primer usuario
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='test-key-6'
        )
        
        # Intentar recuperar con el otro usuario
        retrieved_order = OrderService.get_order_by_id(order.id, other_user.id)
        
        # Debe retornar None
        self.assertIsNone(retrieved_order) 