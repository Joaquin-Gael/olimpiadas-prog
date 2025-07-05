"""
Tests para casos edge y errores del sistema de órdenes.
Paso 5: Validar casos límite, errores y validaciones que faltan.
"""
import pytest
from decimal import Decimal, InvalidOperation
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
    OrderService,
    InvalidCartStateError,
    OrderCreationError
)


class OrderEdgeCasesTestCase(TestCase):
    """
    Tests para casos edge y errores del sistema de órdenes.
    Paso 5: Validar casos límite y errores.
    """
    
    def setUp(self):
        """Configuración para tests de casos edge"""
        # Usuario
        self.user = Users.objects.create_user(
            email='edge@test.com', 
            password='1234', 
            first_name='Edge', 
            last_name='Test', 
            telephone='123456789'
        )
        
        # Paquete
        self.package = Packages.objects.create(
            name='Paquete Edge', 
            description='Paquete para casos edge', 
            final_price=Decimal('100.00')
        )
        
        # Proveedor
        self.supplier = Suppliers.objects.create(
            first_name='Proveedor',
            last_name='Edge',
            organization_name='Organización Edge',
            description='Proveedor para casos edge',
            street='Calle Edge',
            street_number=999,
            city='Ciudad Edge',
            country='País Edge',
            email='edge@proveedor.com',
            telephone='999999999',
            website='https://edge.com'
        )
        
        # ContentType
        self.content_type = ContentType.objects.create(
            app_label='products', 
            model='edge_product'
        )
        
        # Metadata
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
        
        # Componente
        self.component = ComponentPackages.objects.create(
            package=self.package,
            product_metadata=self.metadata,
            order=1
        )

    # ==================== VALIDACIONES DE MODELOS ====================

    def test_1_order_total_negative_validation(self):
        """
        Test 1: Validar que no se puede crear orden con total negativo.
        """
        with self.assertRaises(ValidationError):
            order = Orders(
                user=self.user,
                date=timezone.now(),
                state=OrderState.PENDING,
                total=Decimal('-100.00'),
                idempotency_key='test-negative'
            )
            order.full_clean()

    def test_2_order_total_zero_validation(self):
        """
        Test 2: Validar que se puede crear orden con total cero.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('0.00'),
            idempotency_key='test-zero'
        )
        self.assertEqual(order.total, Decimal('0.00'))

    def test_3_order_details_quantity_zero_validation(self):
        """
        Test 3: Validar que no se puede crear OrderDetails con cantidad cero.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='test-details-zero'
        )
        
        with self.assertRaises(ValidationError):
            detail = OrderDetails(
                order=order,
                product_metadata=self.metadata,
                package=self.package,
                availability_id=1,
                quantity=0,
                unit_price=Decimal('50.00'),
                subtotal=Decimal('0.00'),
                discount_applied=Decimal('0.00')
            )
            detail.full_clean()

    def test_4_order_details_negative_price_validation(self):
        """
        Test 4: Validar que no se puede crear OrderDetails con precio negativo.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='test-negative-price'
        )
        
        with self.assertRaises(ValidationError):
            detail = OrderDetails(
                order=order,
                product_metadata=self.metadata,
                package=self.package,
                availability_id=1,
                quantity=1,
                unit_price=Decimal('-50.00'),
                subtotal=Decimal('-50.00'),
                discount_applied=Decimal('0.00')
            )
            detail.full_clean()

    def test_5_cart_item_duplicate_availability(self):
        """
        Test 5: Validar que no se puede agregar el mismo availability_id dos veces al carrito.
        """
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('100.00'),
            items_cnt=1
        )
        
        # Primer item
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('50.00'),
            currency='USD',
            config={}
        )
        
        # Intentar agregar el mismo availability_id
        with self.assertRaises(IntegrityError):
            CartItem.objects.create(
                cart=cart,
                availability_id=1,  # Mismo availability_id
                product_metadata_id=self.metadata.id,
                qty=1,
                unit_price=Decimal('50.00'),
                currency='USD',
                config={}
            )

    # ==================== CASOS EDGE DE SERVICIOS ====================

    def test_6_create_order_cart_not_found(self):
        """
        Test 6: Validar error cuando el carrito no existe.
        """
        with self.assertRaises(Cart.DoesNotExist):
            create_order_from_cart(99999, self.user.id, idempotency_key='test-not-found')

    def test_7_create_order_cart_wrong_user(self):
        """
        Test 7: Validar error cuando el carrito pertenece a otro usuario.
        """
        # Crear otro usuario
        other_user = Users.objects.create_user(
            email='other@test.com',
            password='1234',
            first_name='Other',
            last_name='User',
            telephone='987654321'
        )
        
        # Crear carrito para el primer usuario
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
            unit_price=Decimal('50.00'),
            currency='USD',
            config={}
        )
        
        # Intentar crear orden con otro usuario
        with self.assertRaises(Cart.DoesNotExist):
            create_order_from_cart(cart.id, other_user.id, idempotency_key='test-wrong-user')

    def test_8_create_order_cart_closed(self):
        """
        Test 8: Validar error cuando el carrito está cerrado.
        """
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.ORDERED,  # Carrito cerrado
            currency='USD',
            total=Decimal('100.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=1,
            product_metadata_id=self.metadata.id,
            qty=1,
            unit_price=Decimal('50.00'),
            currency='USD',
            config={}
        )
        
        # Intentar crear orden desde carrito cerrado
        with self.assertRaises(Cart.DoesNotExist):
            create_order_from_cart(cart.id, self.user.id, idempotency_key='test-closed-cart')

    def test_9_create_order_empty_cart(self):
        """
        Test 9: Validar error cuando el carrito está vacío.
        """
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('0.00'),
            items_cnt=0  # Carrito vacío
        )
        
        # Intentar crear orden desde carrito vacío
        with self.assertRaises(InvalidCartStateError):
            create_order_from_cart(cart.id, self.user.id, idempotency_key='test-empty-cart')

    def test_10_create_order_missing_component_package(self):
        """
        Test 10: Validar comportamiento cuando falta ComponentPackages.
        """
        # Crear metadata sin ComponentPackages
        metadata_no_component = ProductsMetadata.objects.create(
            supplier=self.supplier,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30),
            content_type_id=self.content_type,
            object_id=2,
            unit_price=Decimal('75.00'),
            currency='USD',
            is_active=True
        )
        
        cart = Cart.objects.create(
            user=self.user,
            status=CartStatus.OPEN,
            currency='USD',
            total=Decimal('75.00'),
            items_cnt=1
        )
        
        CartItem.objects.create(
            cart=cart,
            availability_id=2,
            product_metadata_id=metadata_no_component.id,
            qty=1,
            unit_price=Decimal('75.00'),
            currency='USD',
            config={}
        )
        
        # ✅ SOLUCIÓN: Ahora debe funcionar con package_id=None
        order = create_order_from_cart(cart.id, self.user.id, idempotency_key='test-no-component')
        
        # Validar que se creó la orden pero sin package
        order_detail = OrderDetails.objects.get(order=order)
        self.assertIsNone(order_detail.package_id)

    # ==================== CASOS EDGE DE ESTADOS ====================

    def test_11_cancel_order_not_found(self):
        """
        Test 11: Validar error al cancelar orden inexistente.
        """
        with self.assertRaises(Orders.DoesNotExist):
            cancel_order(99999, self.user.id)

    def test_12_pay_order_not_found(self):
        """
        Test 12: Validar error al pagar orden inexistente.
        """
        with self.assertRaises(Orders.DoesNotExist):
            pay_order(99999, self.user.id, 'CREDIT_CARD')

    def test_13_refund_order_not_found(self):
        """
        Test 13: Validar error al reembolsar orden inexistente.
        """
        with self.assertRaises(Orders.DoesNotExist):
            refund_order(99999, self.user.id)

    def test_14_cancel_order_already_cancelled(self):
        """
        Test 14: Validar error al cancelar orden ya cancelada.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.CANCELLED,
            total=Decimal('100.00'),
            idempotency_key='test-already-cancelled'
        )
        
        with self.assertRaises(InvalidCartStateError):
            cancel_order(order.id, self.user.id)

    def test_15_pay_order_already_paid(self):
        """
        Test 15: Validar error al pagar orden ya pagada.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.CONFIRMED,
            total=Decimal('100.00'),
            idempotency_key='test-already-paid'
        )
        
        with self.assertRaises(InvalidCartStateError):
            pay_order(order.id, self.user.id, 'CREDIT_CARD')

    def test_16_refund_order_already_refunded(self):
        """
        Test 16: Validar error al reembolsar orden ya reembolsada.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.REFUNDED,
            total=Decimal('100.00'),
            idempotency_key='test-already-refunded'
        )
        
        with self.assertRaises(InvalidCartStateError):
            refund_order(order.id, self.user.id)

    # ==================== CASOS EDGE DE IDEMPOTENCIA ====================

    def test_17_duplicate_idempotency_key_order(self):
        """
        Test 17: Validar que no se puede crear orden con idempotency_key duplicado.
        """
        # Crear primera orden
        Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='duplicate-key'
        )
        
        # Intentar crear segunda orden con la misma clave
        with self.assertRaises(IntegrityError):
            Orders.objects.create(
                user=self.user,
                date=timezone.now(),
                state=OrderState.PENDING,
                total=Decimal('200.00'),
                idempotency_key='duplicate-key'
            )

    def test_18_idempotency_key_null_allowed(self):
        """
        Test 18: Validar que se puede crear orden sin idempotency_key.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key=None
        )
        
        self.assertIsNone(order.idempotency_key)

    # ==================== CASOS EDGE DE CÁLCULOS ====================

    def test_19_order_details_subtotal_calculation(self):
        """
        Test 19: Validar cálculo correcto de subtotal en OrderDetails.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('150.00'),
            idempotency_key='test-subtotal'
        )
        
        # Crear detalle con descuento
        detail = OrderDetails.objects.create(
            order=order,
            product_metadata=self.metadata,
            package=self.package,
            availability_id=1,
            quantity=2,
            unit_price=Decimal('50.00'),
            subtotal=Decimal('100.00'),  # 2 * 50
            discount_applied=Decimal('10.00')
        )
        
        # Validar cálculos
        expected_subtotal = Decimal('100.00')  # 2 * 50
        self.assertEqual(detail.subtotal, expected_subtotal)

    def test_20_order_details_with_discount(self):
        """
        Test 20: Validar OrderDetails con descuento aplicado.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('90.00'),
            idempotency_key='test-discount'
        )
        
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
        
        self.assertEqual(detail.discount_applied, Decimal('10.00'))

    # ==================== CASOS EDGE DE CONCURRENCIA ====================

    def test_21_concurrent_order_creation_same_cart(self):
        """
        Test 21: Validar comportamiento con creación concurrente de órdenes.
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
        order1 = create_order_from_cart(cart.id, self.user.id, idempotency_key='concurrent-1')
        
        # Intentar crear segunda orden con el mismo carrito
        with self.assertRaises(Cart.DoesNotExist):
            create_order_from_cart(cart.id, self.user.id, idempotency_key='concurrent-2')

    # ==================== CASOS EDGE DE DATOS INVALIDOS ====================

    def test_22_invalid_decimal_values(self):
        """
        Test 22: Validar manejo de valores decimales inválidos.
        """
        with self.assertRaises(InvalidOperation):
            Orders.objects.create(
                user=self.user,
                date=timezone.now(),
                state=OrderState.PENDING,
                total=Decimal('invalid'),
                idempotency_key='test-invalid-decimal'
            )

    def test_23_empty_string_idempotency_key(self):
        """
        Test 23: Validar que se puede crear orden con idempotency_key vacío.
        """
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key=''
        )
        
        self.assertEqual(order.idempotency_key, '')

    def test_24_very_long_idempotency_key(self):
        """
        Test 24: Validar límite de longitud de idempotency_key.
        """
        long_key = 'a' * 64  # Máximo permitido
        order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key=long_key
        )
        
        self.assertEqual(order.idempotency_key, long_key)

    def test_25_too_long_idempotency_key(self):
        """
        Test 25: Validar error con idempotency_key muy largo.
        """
        too_long_key = 'a' * 65  # Más del máximo permitido
        
        # ✅ SOLUCIÓN: Usar el flujo correcto de Django
        with self.assertRaises(ValidationError):
            order = Orders(
                user=self.user,
                date=timezone.now(),
                state=OrderState.PENDING,
                total=Decimal('100.00'),
                idempotency_key=too_long_key
            )
            order.full_clean()  # ✅ Aquí se ejecutan las validaciones 