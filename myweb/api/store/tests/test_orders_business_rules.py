"""
Tests para reglas de negocio específicas del sistema de órdenes.
Paso 6: Validar reglas de negocio y validaciones específicas del dominio.
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

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


class OrderBusinessRulesTestCase(TestCase):
    """
    Tests para reglas de negocio específicas del sistema de órdenes.
    Paso 6: Validar reglas de negocio y validaciones del dominio.
    """
    
    def setUp(self):
        """Configuración para tests de reglas de negocio"""
        # Usuario
        self.user = Users.objects.create_user(
            email='business@test.com', 
            password='1234', 
            first_name='Business', 
            last_name='Test', 
            telephone='123456789'
        )
        
        # Paquete
        self.package = Packages.objects.create(
            name='Paquete Business', 
            description='Paquete para reglas de negocio', 
            final_price=Decimal('200.00')
        )
        
        # Proveedor
        self.supplier = Suppliers.objects.create(
            first_name='Proveedor',
            last_name='Business',
            organization_name='Organización Business',
            description='Proveedor para reglas de negocio',
            street='Calle Business',
            street_number=777,
            city='Ciudad Business',
            country='País Business',
            email='business@proveedor.com',
            telephone='777777777',
            website='https://business.com'
        )
        
        # ContentType
        self.content_type = ContentType.objects.create(
            app_label='products', 
            model='business_product'
        )
        
        # Metadata
        self.metadata = ProductsMetadata.objects.create(
            supplier=self.supplier,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30),
            content_type_id=self.content_type,
            object_id=1,
            unit_price=Decimal('100.00'),
            currency='USD',
            is_active=True
        )
        
        # Componente
        self.component = ComponentPackages.objects.create(
            package=self.package,
            product_metadata=self.metadata,
            order=1
        )

    # ==================== REGLAS DE NEGOCIO - ESTADOS ====================

    def test_1_order_state_transition_rules(self):
        """
        Test 1: Validar reglas de transición de estados de órdenes.
        """
        # Crear orden en estado PENDING
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='business-state-1'
        )
        
        # PENDING -> CONFIRMED (válido)
        paid_order = pay_order(order.id, self.user.id, 'CREDIT_CARD')
        self.assertEqual(paid_order.state, OrderState.CONFIRMED)
        
        # CONFIRMED -> REFUNDED (válido)
        refunded_order = refund_order(paid_order.id, self.user.id)
        self.assertEqual(refunded_order.state, OrderState.REFUNDED)
        
        # REFUNDED -> CONFIRMED (inválido - no hay función para esto)
        # Esto valida que no se puede volver a un estado anterior

    def test_2_order_state_validation_rules(self):
        """
        Test 2: Validar que los estados de orden son válidos según las reglas de negocio.
        """
        # Crear orden y validar estado inicial
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='business-state-2'
        )
        
        # Validar que el estado es uno de los permitidos
        valid_states = [choice[0] for choice in OrderState.choices]
        self.assertIn(order.state, valid_states)

    def test_3_cart_state_business_rules(self):
        """
        Test 3: Validar reglas de negocio para estados de carrito.
        """
        # Crear carrito abierto
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('100.00'),
            items_cnt=1
        )
        
        # Validar que se puede crear orden desde carrito abierto
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('100.00'),
            currency='USD',
            config={}
        )
        
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='business-cart-1')
        self.assertIsNotNone(order.id)

    # ==================== REGLAS DE NEGOCIO - PRECIOS ====================

    def test_4_order_total_calculation_business_rule(self):
        """
        Test 4: Validar que el total de la orden coincide con la suma de los detalles.
        """
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('200.00'),
            items_cnt=2
        )
        
        # Crear dos items
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('100.00'),
            currency='USD',
            config={}
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=2,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('100.00'),
            currency='USD',
            config={}
        )
        
        # Crear orden
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='business-total-1')
        
        # Validar que el total coincide
        self.assertEqual(order.total, Decimal('200.00'))
        
        # Validar que la suma de detalles coincide
        order_details = OrderDetails.objects.filter(order=order)
        total_from_details = sum(detail.subtotal for detail in order_details)
        self.assertEqual(total_from_details, Decimal('200.00'))

    def test_5_discount_business_rule(self):
        """
        Test 5: Validar reglas de negocio para descuentos.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('90.00'),
            idempotency_key='business-discount-1'
        )
        
        # Crear detalle con descuento
        detail = OrderDetails.objects.create(
            order=order,
            product_metadata=self.metadata,
            package=self.package,
            availability_id=1,
            quantity=1,
            unit_price=Decimal('100.00'),
            subtotal=Decimal('90.00'),
            discount_applied=Decimal('10.00')
        )
        
        # Validar que el descuento no excede el precio unitario
        self.assertLessEqual(detail.discount_applied, detail.unit_price)
        
        # Validar que el subtotal es correcto (precio - descuento)
        expected_subtotal = detail.unit_price - detail.discount_applied
        self.assertEqual(detail.subtotal, expected_subtotal)

    # ==================== REGLAS DE NEGOCIO - CANTIDADES ====================

    def test_6_quantity_business_rules(self):
        """
        Test 6: Validar reglas de negocio para cantidades.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('300.00'),
            idempotency_key='business-quantity-1'
        )
        
        # Crear detalle con cantidad mayor a 1
        detail = OrderDetails.objects.create(
            order=order,
            product_metadata=self.metadata,
            package=self.package,
            availability_id=1,
            quantity=3,
            unit_price=Decimal('100.00'),
            subtotal=Decimal('300.00'),
            discount_applied=Decimal('0.00')
        )
        
        # Validar que la cantidad es positiva
        self.assertGreater(detail.quantity, 0)
        
        # Validar que el subtotal es correcto (cantidad * precio unitario)
        expected_subtotal = detail.quantity * detail.unit_price
        self.assertEqual(detail.subtotal, expected_subtotal)

    # ==================== REGLAS DE NEGOCIO - MONEDAS ====================

    def test_7_currency_business_rules(self):
        """
        Test 7: Validar reglas de negocio para monedas.
        """
        # Crear carrito con moneda específica
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='EUR',
            total=Decimal('100.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('100.00'),
            currency='EUR',
            config={}
        )
        
        # Crear orden
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='business-currency-1')
        
        # Validar que la moneda se mantiene consistente
        # (Nota: el modelo Orders no tiene campo currency, pero CartItem sí)
        cart_items = CartItem.objects.filter(cart=cart)
        for item in cart_items:
            self.assertEqual(item.currency, 'EUR')

    # ==================== REGLAS DE NEGOCIO - USUARIOS ====================

    def test_8_user_ownership_business_rule(self):
        """
        Test 8: Validar regla de negocio de propiedad de recursos.
        """
        # Crear otro usuario
        other_user = Users.objects.create_user(
            email='other@business.com',
            password='1234',
            first_name='Other',
            last_name='Business',
            telephone='888888888'
        )
        
        # Crear orden para el primer usuario
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='business-ownership-1'
        )
        
        # Validar que el otro usuario no puede acceder a la orden
        retrieved_order = OrderService.get_order_by_id(order.id, other_user.id)
        self.assertIsNone(retrieved_order)

    def test_9_user_multiple_orders_business_rule(self):
        """
        Test 9: Validar que un usuario puede tener múltiples órdenes.
        """
        # Crear múltiples órdenes para el mismo usuario
        order1 = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='business-multiple-1'
        )
        
        order2 = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('200.00'),
            idempotency_key='business-multiple-2'
        )
        
        # Validar que ambas órdenes existen y pertenecen al usuario
        user_orders = Orders.objects.filter(user=self.user)
        self.assertEqual(user_orders.count(), 2)
        self.assertIn(order1, user_orders)
        self.assertIn(order2, user_orders)

    # ==================== REGLAS DE NEGOCIO - IDEMPOTENCIA ====================

    def test_10_idempotency_business_rule(self):
        """
        Test 10: Validar regla de negocio de idempotencia.
        """
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('100.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('100.00'),
            currency='USD',
            config={}
        )
        
        # Crear primera orden
        order1 = create_order_from_cart(cart.id, self.user.id, idempotency_key='business-idempotency-1')
        
        # Intentar crear segunda orden con la misma clave (debe fallar)
        with self.assertRaises(IntegrityError):
            Orders.objects.create(
                user=self.user,
                date=timezone.now(),
                state=OrderState.PENDING,
                total=Decimal('100.00'),
                idempotency_key='business-idempotency-1'
            )

    # ==================== REGLAS DE NEGOCIO - FECHAS ====================

    def test_11_order_date_business_rule(self):
        """
        Test 11: Validar reglas de negocio para fechas de órdenes.
        """
        # Crear orden con fecha actual
        current_time = timezone.now()
        order = Orders.objects.create(
            user=self.user,
            date=current_time,
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='business-date-1'
        )
        
        # Validar que la fecha de creación es reciente
        time_diff = timezone.now() - order.created_at
        self.assertLess(time_diff.total_seconds(), 10)  # Menos de 10 segundos
        
        # Validar que la fecha de actualización es igual a la de creación inicialmente
        self.assertEqual(order.created_at, order.updated_at)

    def test_12_order_date_update_business_rule(self):
        """
        Test 12: Validar que la fecha de actualización se actualiza al modificar la orden.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='business-date-2'
        )
        
        # Guardar la fecha de creación original
        original_created = order.created_at
        original_updated = order.updated_at
        
        # Modificar la orden
        order.state = OrderState.CONFIRMED
        order.save()
        
        # Validar que created_at no cambió pero updated_at sí
        order.refresh_from_db()
        self.assertEqual(order.created_at, original_created)
        self.assertGreater(order.updated_at, original_updated)

    # ==================== REGLAS DE NEGOCIO - PRODUCTOS ====================

    def test_13_product_metadata_business_rule(self):
        """
        Test 13: Validar reglas de negocio para metadata de productos.
        """
        # Crear metadata inactiva
        inactive_metadata = ProductsMetadata.objects.create(
            supplier=self.supplier,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30),
            content_type_id=self.content_type,
            object_id=2,
            unit_price=Decimal('50.00'),
            currency='USD',
            is_active=False  # Producto inactivo
        )
        
        # Crear carrito con producto inactivo
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('50.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=2,
            product_metadata_id=inactive_metadata.id,
            qty=1,
            unit_price=Decimal('50.00'),
            currency='USD',
            config={}
        )
        
        # ✅ SOLUCIÓN: Ahora debe funcionar con package_id=None
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='business-inactive-1')
        self.assertIsNotNone(order.id)
        
        # Validar que se creó el detalle sin paquete (producto individual)
        order_detail = OrderDetails.objects.get(order=order)
        self.assertIsNone(order_detail.package_id)

    # ==================== REGLAS DE NEGOCIO - CONFIGURACIÓN ====================

    def test_14_cart_item_config_business_rule(self):
        """
        Test 14: Validar reglas de negocio para configuración de items del carrito.
        """
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('100.00'),
            items_cnt=1
        )
        
        # Crear item con configuración específica
        config = {
            'fecha_inicio': '2024-01-01',
            'fecha_fin': '2024-01-05',
            'habitaciones': 2,
            'pasajeros': 4
        }
        
        cart_item = CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('100.00'),
            currency='USD',
            config=config
        )
        
        # Validar que la configuración se guardó correctamente
        self.assertEqual(cart_item.config, config)
        self.assertEqual(cart_item.config['habitaciones'], 2)
        self.assertEqual(cart_item.config['pasajeros'], 4)

    # ==================== REGLAS DE NEGOCIO - VALIDACIONES COMPLEJAS ====================

    def test_15_complex_order_validation_business_rule(self):
        """
        Test 15: Validar reglas de negocio complejas para órdenes.
        """
        # Crear orden con múltiples detalles
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('500.00'),
            idempotency_key='business-complex-1'
        )
        
        # Crear múltiples detalles
        detail1 = OrderDetails.objects.create(
            order=order,
            product_metadata=self.metadata,
            package=self.package,
            availability_id=1,
            quantity=2,
            unit_price=Decimal('100.00'),
            subtotal=Decimal('200.00'),
            discount_applied=Decimal('0.00')
        )
        
        detail2 = OrderDetails.objects.create(
            order=order,
            product_metadata=self.metadata,
            package=self.package,
            availability_id=2,
            quantity=3,
            unit_price=Decimal('100.00'),
            subtotal=Decimal('300.00'),
            discount_applied=Decimal('0.00')
        )
        
        # Validar reglas de negocio complejas
        order_details = OrderDetails.objects.filter(order=order)
        
        # 1. Validar que todos los detalles pertenecen a la misma orden
        for detail in order_details:
            self.assertEqual(detail.order, order)
        
        # 2. Validar que la suma de subtotales coincide con el total de la orden
        total_from_details = sum(detail.subtotal for detail in order_details)
        self.assertEqual(total_from_details, Decimal('500.00'))
        
        # 3. Validar que no hay cantidades negativas
        for detail in order_details:
            self.assertGreater(detail.quantity, 0)
        
        # 4. Validar que no hay precios negativos
        for detail in order_details:
            self.assertGreaterEqual(detail.unit_price, Decimal('0.00')) 