"""
Tests de integración para el flujo completo de órdenes.
Paso 4: Validar el flujo completo desde creación hasta finalización.
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from api.users.models import Users
from api.store.models import Cart, CartItem, Orders, OrderDetails, OrderState, CartStatus
from api.products.models import Packages, ProductsMetadata, ComponentPackages, Suppliers
from api.store.services.services_orders import (
    create_order_from_cart, 
    cancel_order, 
    pay_order, 
    refund_order, 
    OrderService
)


class OrderIntegrationTestCase(TestCase):
    """
    Tests de integración para el flujo completo de órdenes.
    Paso 4: Validar el flujo completo end-to-end.
    """
    
    def setUp(self):
        """Configuración para tests de integración"""
        # Usuario
        self.user = Users.objects.create_user(
            email='integration@test.com', 
            password='1234', 
            first_name='Integration', 
            last_name='Test', 
            telephone='123456789'
        )
        
        # Paquete turístico completo
        self.package = Packages.objects.create(
            name='Paquete Completo Turístico', 
            description='Paquete que incluye vuelo, hotel y actividades', 
            final_price=Decimal('1500.00')
        )
        
        # Proveedor
        self.supplier = Suppliers.objects.create(
            first_name='Agencia',
            last_name='Integración',
            organization_name='Turismo Integral',
            description='Agencia de viajes completa',
            street='Av. Integración',
            street_number=789,
            city='Ciudad Integración',
            country='País Integración',
            email='info@integracion.com',
            telephone='555123456',
            website='https://integracion.com'
        )
        
        # ContentType
        self.content_type = ContentType.objects.create(
            app_label='products', 
            model='integrated_product'
        )
        
        # Metadata del producto
        self.metadata = ProductsMetadata.objects.create(
            supplier=self.supplier,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=90),
            content_type_id=self.content_type,
            object_id=1,
            unit_price=Decimal('1200.00'),
            currency='USD',
            is_active=True
        )
        
        # Componente del paquete
        self.component = ComponentPackages.objects.create(
            package=self.package,
            product_metadata=self.metadata,
            order=1
        )

    def test_1_complete_order_lifecycle_success(self):
        """
        Test 1: Flujo completo exitoso de una orden.
        Cart -> Order -> Payment -> Completion
        """
        # 1. Crear carrito
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('1200.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('1200.00'),
            currency='USD',
            config={}
        )
        
        # 2. Crear orden desde carrito
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='integration-1')
        
        # Validar orden creada
        self.assertEqual(order.state, OrderState.PENDING)
        self.assertEqual(order.total, Decimal('1200.00'))
        
        # Validar detalles creados
        order_details = OrderDetails.objects.filter(order=order)
        self.assertEqual(order_details.count(), 1)
        self.assertEqual(order_details.first().product_metadata, self.metadata)
        
        # 3. Pagar orden
        paid_order = pay_order(order.id, self.user.id, 'CREDIT_CARD')
        self.assertEqual(paid_order.state, OrderState.CONFIRMED)
        
        # 4. Simular completación (en un caso real esto vendría de otro proceso)
        paid_order.state = OrderState.COMPLETED
        paid_order.save()
        
        # Validar estado final
        final_order = Orders.objects.get(id=order.id)
        self.assertEqual(final_order.state, OrderState.COMPLETED)

    def test_2_complete_order_lifecycle_with_cancellation(self):
        """
        Test 2: Flujo completo con cancelación.
        Cart -> Order -> Cancellation
        """
        # 1. Crear carrito
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('1200.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('1200.00'),
            currency='USD',
            config={}
        )
        
        # 2. Crear orden
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='integration-2')
        self.assertEqual(order.state, OrderState.PENDING)
        
        # 3. Cancelar orden
        cancelled_order = cancel_order(order.id, self.user.id)
        self.assertEqual(cancelled_order.state, OrderState.CANCELLED)

    def test_3_complete_order_lifecycle_with_refund(self):
        """
        Test 3: Flujo completo con reembolso.
        Cart -> Order -> Payment -> Refund
        """
        # 1. Crear carrito
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('1200.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('1200.00'),
            currency='USD',
            config={}
        )
        
        # 2. Crear orden
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='integration-3')
        
        # 3. Pagar orden
        paid_order = pay_order(order.id, self.user.id, 'DEBIT_CARD')
        self.assertEqual(paid_order.state, OrderState.CONFIRMED)
        
        # 4. Reembolsar orden
        refunded_order = refund_order(paid_order.id, self.user.id)
        self.assertEqual(refunded_order.state, OrderState.REFUNDED)

    def test_4_multiple_orders_same_user(self):
        """
        Test 4: Múltiples órdenes del mismo usuario.
        Valida que un usuario puede tener múltiples órdenes.
        """
        # Crear múltiples carritos y órdenes
        orders = []
        
        for i in range(3):
            # Carrito
            cart = Cart.objects.create(
                user=self.user,
                status=CartStatus.OPEN,
                currency='USD',
                total=Decimal('1200.00'),
                items_cnt=1
            )
            
            CartItem.objects.create(
                cart=cart,
                availability_id=i+1,
                product_metadata_id=self.metadata.id,
                qty=1,
                unit_price=Decimal('1200.00'),
                currency='USD',
                config={}
            )
            
            # Orden
            order = create_order_from_cart(
                cart.id, 
                self.user.id, 
                idempotency_key=f'integration-multi-{i}'
            )
            orders.append(order)
        
        # Validar que se crearon 3 órdenes
        user_orders = Orders.objects.filter(user=self.user)
        self.assertEqual(user_orders.count(), 3)
        
        # Validar que todas están pendientes
        for order in orders:
            self.assertEqual(order.state, OrderState.PENDING)

    def test_5_order_service_integration(self):
        """
        Test 5: Integración completa con OrderService.
        Valida que todos los métodos del servicio funcionan juntos.
        """
        # 1. Crear carrito y orden
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('1200.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('1200.00'),
            currency='USD',
            config={}
        )
        
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='integration-service')
        
        # 2. Usar OrderService para recuperar
        retrieved_order = OrderService.get_order_by_id(order.id, self.user.id)
        self.assertIsNotNone(retrieved_order)
        self.assertEqual(retrieved_order.id, order.id)
        
        # 3. Usar OrderService para pagar
        paid_order = OrderService.pay_order(order.id, self.user.id, 'CREDIT_CARD')
        self.assertEqual(paid_order.state, OrderState.CONFIRMED)
        
        # 4. Usar OrderService para reembolsar
        refunded_order = OrderService.refund_order(paid_order.id, self.user.id)
        self.assertEqual(refunded_order.state, OrderState.REFUNDED)

    def test_6_error_handling_integration(self):
        """
        Test 6: Manejo de errores en flujo completo.
        Valida que los errores se manejan correctamente.
        """
        # 1. Intentar crear orden desde carrito inexistente
        with self.assertRaises(Exception):
            create_order_from_cart(99999, self.user.id, idempotency_key='error-test')
        
        # 2. Intentar acceder a orden inexistente con OrderService
        retrieved_order = OrderService.get_order_by_id(99999, self.user.id)
        self.assertIsNone(retrieved_order)
        
        # 3. Crear orden válida y luego intentar operaciones inválidas
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('1200.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('1200.00'),
            currency='USD',
            config={}
        )
        
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='error-test-valid')
        
        # Intentar reembolsar orden pendiente (debe fallar)
        with self.assertRaises(Exception):
            refund_order(order.id, self.user.id)

    def test_7_data_consistency_integration(self):
        """
        Test 7: Consistencia de datos en flujo completo.
        Valida que los datos se mantienen consistentes.
        """
        # 1. Crear carrito con múltiples items
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('2400.00'),  # 2 items
            items_cnt=2
        )
        
        # Crear segundo metadata
        metadata2 = ProductsMetadata.objects.create(
            supplier=self.supplier,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=60),
            content_type_id=self.content_type,
            object_id=2,
            unit_price=Decimal('1200.00'),
            currency='USD',
            is_active=True
        )
        
        ComponentPackages.objects.create(
            package=self.package,
            product_metadata=metadata2,
            order=2
        )
        
        # Primer item
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('1200.00'),
            currency='USD',
            config={}
        )
        
        # Segundo item
        CartItem.objects.create(
            cart=cart,
            availability_id=2,
            product_metadata_id=metadata2.id,
            qty=1,
            unit_price=Decimal('1200.00'),
            currency='USD',
            config={}
        )
        
        # 2. Crear orden
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='consistency-test')
        
        # 3. Validar consistencia de datos
        self.assertEqual(order.total, Decimal('2400.00'))
        
        order_details = OrderDetails.objects.filter(order=order)
        self.assertEqual(order_details.count(), 2)
        
        # Validar que los totales coinciden
        total_from_details = sum(detail.subtotal for detail in order_details)
        self.assertEqual(total_from_details, Decimal('2400.00'))
        
        # 4. Pagar y validar consistencia
        paid_order = pay_order(order.id, self.user.id, 'CREDIT_CARD')
        self.assertEqual(paid_order.total, Decimal('2400.00'))
        
        # Los detalles deben mantenerse
        paid_order_details = OrderDetails.objects.filter(order=paid_order)
        self.assertEqual(paid_order_details.count(), 2)

    def test_8_performance_integration(self):
        """
        Test 8: Rendimiento en flujo completo.
        Valida que el flujo es eficiente.
        """
        import time
        
        # Medir tiempo de creación de orden
        start_time = time.time()
        
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('1200.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('1200.00'),
            currency='USD',
            config={}
        )
        
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='performance-test')
        
        creation_time = time.time() - start_time
        
        # Validar que la creación es rápida (menos de 1 segundo)
        self.assertLess(creation_time, 1.0)
        
        # Medir tiempo de operaciones de estado
        start_time = time.time()
        paid_order = pay_order(order.id, self.user.id, 'CREDIT_CARD')
        payment_time = time.time() - start_time
        
        # Validar que el pago es rápido
        self.assertLess(payment_time, 1.0)
        
        # Medir tiempo de reembolso
        start_time = time.time()
        refunded_order = refund_order(paid_order.id, self.user.id)
        refund_time = time.time() - start_time
        
        # Validar que el reembolso es rápido
        self.assertLess(refund_time, 1.0) 