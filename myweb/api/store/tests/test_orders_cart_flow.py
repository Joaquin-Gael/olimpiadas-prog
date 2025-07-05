"""
Tests para el flujo completo de creación de órdenes desde carritos.
Paso 2: Validar que el flujo cart -> order funciona correctamente.
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from api.users.models import Users
from api.store.models import Cart, CartItem, Orders, OrderDetails, OrderState, CartStatus
from api.products.models import Packages, ProductsMetadata, ComponentPackages, Suppliers
from api.store.services.services_orders import create_order_from_cart, OrderService


class OrderCartFlowTestCase(TestCase):
    """
    Tests para el flujo de creación de órdenes desde carritos.
    Paso 2: Validar el flujo completo cart -> order.
    """
    
    def setUp(self):
        """Configuración para tests de flujo de carrito"""
        # Usuario
        self.user = Users.objects.create_user(
            email='testuser@example.com', 
            password='1234', 
            first_name='Test', 
            last_name='User', 
            telephone='123456789'
        )
        
        # Paquete
        self.package = Packages.objects.create(
            name='Paquete Turístico', 
            description='Paquete completo de turismo', 
            final_price=Decimal('200.00')
        )
        
        # Proveedor
        self.supplier = Suppliers.objects.create(
            first_name='Agencia',
            last_name='Turística',
            organization_name='Turismo Express',
            description='Agencia de viajes',
            street='Av. Principal',
            street_number=456,
            city='Ciudad Turística',
            country='País Turístico',
            email='info@turismo.com',
            telephone='987654321',
            website='https://turismo.com'
        )
        
        # ContentType
        self.content_type = ContentType.objects.create(
            app_label='products', 
            model='tour_package'
        )
        
        # Metadata del producto
        self.metadata = ProductsMetadata.objects.create(
            supplier=self.supplier,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=60),
            content_type_id=self.content_type,
            object_id=1,
            unit_price=Decimal('150.00'),
            currency='USD',
            is_active=True
        )
        
        # Componente del paquete
        self.component = ComponentPackages.objects.create(
            package=self.package,
            product_metadata=self.metadata,
            order=1
        )

    def test_1_create_order_from_single_item_cart(self):
        """
        Test 1: Crear orden desde carrito con un solo item.
        Valida el flujo básico cart -> order.
        """
        # Crear carrito con un item
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('150.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('150.00'),
            currency='USD',
            config={}
        )
        
        # Crear orden desde carrito
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='test-flow-1')
        
        # Validaciones de la orden
        self.assertIsNotNone(order.id)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.state, OrderState.PENDING)
        self.assertEqual(order.total, Decimal('150.00'))
        self.assertEqual(order.idempotency_key, 'test-flow-1')
        
        # Validar que se crearon los detalles de la orden
        order_details = OrderDetails.objects.filter(order=order)
        self.assertEqual(order_details.count(), 1)
        
        detail = order_details.first()
        self.assertEqual(detail.product_metadata, self.metadata)
        self.assertEqual(detail.package, self.package)
        self.assertEqual(detail.quantity, 1)
        self.assertEqual(detail.unit_price, Decimal('150.00'))
        self.assertEqual(detail.subtotal, Decimal('150.00'))

    def test_2_create_order_from_multi_item_cart(self):
        """
        Test 2: Crear orden desde carrito con múltiples items.
        Valida que se pueden procesar múltiples items.
        """
        # Crear segundo metadata para otro producto
        metadata2 = ProductsMetadata.objects.create(
            supplier=self.supplier,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30),
            content_type_id=self.content_type,
            object_id=2,
            unit_price=Decimal('75.00'),
            currency='USD',
            is_active=True
        )
        
        # Crear segundo componente
        ComponentPackages.objects.create(
            package=self.package,
            product_metadata=metadata2,
            order=2
        )
        
        # Crear carrito con dos items
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('225.00'),  # 150 + 75
            items_cnt=2
        )
        
        # Primer item
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('150.00'),
            currency='USD',
            config={}
        )
        
        # Segundo item
        CartItem.objects.create(
            cart=cart,
            availability_id=2,
            product_metadata_id=metadata2.id,
            qty=1,
            unit_price=Decimal('75.00'),
            currency='USD',
            config={}
        )
        
        # Crear orden
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='test-flow-2')
        
        # Validaciones
        self.assertEqual(order.total, Decimal('225.00'))
        
        # Validar que se crearon dos detalles
        order_details = OrderDetails.objects.filter(order=order)
        self.assertEqual(order_details.count(), 2)
        
        # Verificar que ambos productos están en los detalles
        product_metadata_ids = [detail.product_metadata_id for detail in order_details]
        self.assertIn(self.metadata.id, product_metadata_ids)
        self.assertIn(metadata2.id, product_metadata_ids)

    def test_3_create_order_with_quantity_greater_than_one(self):
        """
        Test 3: Crear orden con cantidad mayor a 1.
        Valida el cálculo correcto de subtotales.
        """
        # Crear carrito con cantidad 3
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('450.00'),  # 150 * 3
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=3,
            unit_price=Decimal('150.00'),
            currency='USD',
            config={}
        )
        
        # Crear orden
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='test-flow-3')
        
        # Validaciones
        self.assertEqual(order.total, Decimal('450.00'))
        
        # Validar detalle
        order_detail = OrderDetails.objects.get(order=order)
        self.assertEqual(order_detail.quantity, 3)
        self.assertEqual(order_detail.unit_price, Decimal('150.00'))
        self.assertEqual(order_detail.subtotal, Decimal('450.00'))

    def test_4_idempotency_key_uniqueness(self):
        """
        Test 4: Validar que las claves de idempotencia son únicas.
        Previene órdenes duplicadas.
        """
        # Crear carrito
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('150.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('150.00'),
            currency='USD',
            config={}
        )
        
        # Crear primera orden
        order1 = create_order_from_cart(cart.id, self.user.id, idempotency_key='unique-key')
        
        # Intentar crear segunda orden con la misma clave
        with self.assertRaises(Exception):  # Debe fallar por clave duplicada
            order2 = create_order_from_cart(cart.id, self.user.id, idempotency_key='unique-key')

    def test_5_empty_cart_validation(self):
        """
        Test 5: Validar que no se puede crear orden desde carrito vacío.
        """
        # Crear carrito vacío
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('0.00'),
            items_cnt=0
        )
        
        # Intentar crear orden desde carrito vacío
        with self.assertRaises(Exception):
            create_order_from_cart(cart.id, self.user.id, idempotency_key='test-empty')

    def test_6_wrong_user_cart_access(self):
        """
        Test 6: Validar que no se puede acceder a carrito de otro usuario.
        """
        # Crear otro usuario
        other_user = Users.objects.create_user(
            email='other@example.com',
            password='1234',
            first_name='Other',
            last_name='User',
            telephone='111111111'
        )
        
        # Crear carrito para el primer usuario
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('150.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('150.00'),
            currency='USD',
            config={}
        )
        
        # Intentar crear orden con otro usuario
        with self.assertRaises(Exception):
            create_order_from_cart(cart.id, other_user.id, idempotency_key='test-wrong-user')

    def test_7_closed_cart_validation(self):
        """
        Test 7: Validar que no se puede crear orden desde carrito cerrado.
        """
        # Crear carrito cerrado
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.ORDERED,  # Carrito ya procesado
            currency='USD',
            total=Decimal('150.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('150.00'),
            currency='USD',
            config={}
        )
        
        # Intentar crear orden desde carrito cerrado
        with self.assertRaises(Exception):
            create_order_from_cart(cart.id, self.user.id, idempotency_key='test-closed-cart') 