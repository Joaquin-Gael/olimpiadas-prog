"""
Tests para las operaciones de cambio de estado de las órdenes.
Paso 3: Validar cancelación, pago, reembolso y transiciones de estado.
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from api.users.models import Users
from api.store.models import Orders, OrderState
from api.store.services.services_orders import cancel_order, pay_order, refund_order, OrderService


class OrderStateOperationsTestCase(TestCase):
    """
    Tests para operaciones de cambio de estado de órdenes.
    Paso 3: Validar transiciones de estado y operaciones.
    """
    
    def setUp(self):
        """Configuración para tests de operaciones de estado"""
        # Usuario
        self.user = Users.objects.create_user(
            email='testuser@example.com', 
            password='1234', 
            first_name='Test', 
            last_name='User', 
            telephone='123456789'
        )
        
        # Orden pendiente
        self.pending_order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('100.00'),
            idempotency_key='test-pending'
        )
        
        # Orden confirmada
        self.confirmed_order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.CONFIRMED,
            total=Decimal('200.00'),
            idempotency_key='test-confirmed'
        )
        
        # Orden completada
        self.completed_order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.COMPLETED,
            total=Decimal('300.00'),
            idempotency_key='test-completed'
        )

    def test_1_cancel_pending_order(self):
        """
        Test 1: Cancelar orden pendiente.
        Valida que se puede cancelar una orden en estado PENDING.
        """
        # Cancelar orden pendiente
        cancelled_order = cancel_order(self.pending_order.id, self.user.id)
        
        # Validaciones
        self.assertEqual(cancelled_order.state, OrderState.CANCELLED)
        self.assertEqual(cancelled_order.id, self.pending_order.id)
        self.assertEqual(cancelled_order.total, Decimal('100.00'))

    def test_2_cancel_confirmed_order(self):
        """
        Test 2: Cancelar orden confirmada.
        Valida que se puede cancelar una orden en estado CONFIRMED.
        """
        # Cancelar orden confirmada
        cancelled_order = cancel_order(self.confirmed_order.id, self.user.id)
        
        # Validaciones
        self.assertEqual(cancelled_order.state, OrderState.CANCELLED)
        self.assertEqual(cancelled_order.id, self.confirmed_order.id)

    def test_3_cannot_cancel_completed_order(self):
        """
        Test 3: No se puede cancelar orden completada.
        Valida que las órdenes completadas no se pueden cancelar.
        """
        # Intentar cancelar orden completada
        with self.assertRaises(Exception):
            cancel_order(self.completed_order.id, self.user.id)

    def test_4_cannot_cancel_already_cancelled_order(self):
        """
        Test 4: No se puede cancelar orden ya cancelada.
        """
        # Cancelar orden primero
        cancelled_order = cancel_order(self.pending_order.id, self.user.id)
        
        # Intentar cancelar de nuevo
        with self.assertRaises(Exception):
            cancel_order(cancelled_order.id, self.user.id)

    def test_5_pay_pending_order(self):
        """
        Test 5: Pagar orden pendiente.
        Valida que se puede marcar como pagada una orden pendiente.
        """
        # Pagar orden pendiente
        paid_order = pay_order(self.pending_order.id, self.user.id, 'CREDIT_CARD')
        
        # Validaciones
        self.assertEqual(paid_order.state, OrderState.CONFIRMED)
        self.assertEqual(paid_order.id, self.pending_order.id)

    def test_6_cannot_pay_confirmed_order(self):
        """
        Test 6: No se puede pagar orden ya confirmada.
        """
        # Intentar pagar orden ya confirmada
        with self.assertRaises(Exception):
            pay_order(self.confirmed_order.id, self.user.id, 'CREDIT_CARD')

    def test_7_cannot_pay_cancelled_order(self):
        """
        Test 7: No se puede pagar orden cancelada.
        """
        # Cancelar orden primero
        cancelled_order = cancel_order(self.pending_order.id, self.user.id)
        
        # Intentar pagar orden cancelada
        with self.assertRaises(Exception):
            pay_order(cancelled_order.id, self.user.id, 'CREDIT_CARD')

    def test_8_refund_confirmed_order(self):
        """
        Test 8: Reembolsar orden confirmada.
        Valida que se puede reembolsar una orden confirmada.
        """
        # Reembolsar orden confirmada
        refunded_order = refund_order(self.confirmed_order.id, self.user.id)
        
        # Validaciones
        self.assertEqual(refunded_order.state, OrderState.REFUNDED)
        self.assertEqual(refunded_order.id, self.confirmed_order.id)

    def test_9_refund_completed_order(self):
        """
        Test 9: Reembolsar orden completada.
        Valida que se puede reembolsar una orden completada.
        """
        # Reembolsar orden completada
        refunded_order = refund_order(self.completed_order.id, self.user.id)
        
        # Validaciones
        self.assertEqual(refunded_order.state, OrderState.REFUNDED)
        self.assertEqual(refunded_order.id, self.completed_order.id)

    def test_10_cannot_refund_pending_order(self):
        """
        Test 10: No se puede reembolsar orden pendiente.
        """
        # Intentar reembolsar orden pendiente
        with self.assertRaises(Exception):
            refund_order(self.pending_order.id, self.user.id)

    def test_11_cannot_refund_already_refunded_order(self):
        """
        Test 11: No se puede reembolsar orden ya reembolsada.
        """
        # Reembolsar orden primero
        refunded_order = refund_order(self.confirmed_order.id, self.user.id)
        
        # Intentar reembolsar de nuevo
        with self.assertRaises(Exception):
            refund_order(refunded_order.id, self.user.id)

    def test_12_refund_partial_amount(self):
        """
        Test 12: Reembolsar monto parcial.
        Valida que se puede reembolsar un monto específico.
        """
        # Reembolsar monto parcial
        partial_refund = Decimal('50.00')
        refunded_order = refund_order(self.confirmed_order.id, self.user.id, partial_refund)
        
        # Validaciones
        self.assertEqual(refunded_order.state, OrderState.REFUNDED)
        self.assertEqual(refunded_order.id, self.confirmed_order.id)

    def test_13_wrong_user_cannot_cancel_order(self):
        """
        Test 13: Usuario incorrecto no puede cancelar orden.
        """
        # Crear otro usuario
        other_user = Users.objects.create_user(
            email='other@example.com',
            password='1234',
            first_name='Other',
            last_name='User',
            telephone='987654321'
        )
        
        # Intentar cancelar orden con usuario incorrecto
        with self.assertRaises(Exception):
            cancel_order(self.pending_order.id, other_user.id)

    def test_14_wrong_user_cannot_pay_order(self):
        """
        Test 14: Usuario incorrecto no puede pagar orden.
        """
        # Crear otro usuario
        other_user = Users.objects.create_user(
            email='other@example.com',
            password='1234',
            first_name='Other',
            last_name='User',
            telephone='987654321'
        )
        
        # Intentar pagar orden con usuario incorrecto
        with self.assertRaises(Exception):
            pay_order(self.pending_order.id, other_user.id, 'CREDIT_CARD')

    def test_15_wrong_user_cannot_refund_order(self):
        """
        Test 15: Usuario incorrecto no puede reembolsar orden.
        """
        # Crear otro usuario
        other_user = Users.objects.create_user(
            email='other@example.com',
            password='1234',
            first_name='Other',
            last_name='User',
            telephone='987654321'
        )
        
        # Intentar reembolsar orden con usuario incorrecto
        with self.assertRaises(Exception):
            refund_order(self.confirmed_order.id, other_user.id)

    def test_16_order_service_cancel_order(self):
        """
        Test 16: Probar OrderService.cancel_order.
        Valida que el servicio funciona correctamente.
        """
        # Usar el servicio para cancelar
        cancelled_order = OrderService.cancel_order(self.pending_order.id, self.user.id)
        
        # Validaciones
        self.assertEqual(cancelled_order.state, OrderState.CANCELLED)
        self.assertEqual(cancelled_order.id, self.pending_order.id)

    def test_17_order_service_pay_order(self):
        """
        Test 17: Probar OrderService.pay_order.
        Valida que el servicio funciona correctamente.
        """
        # Usar el servicio para pagar
        paid_order = OrderService.pay_order(self.pending_order.id, self.user.id, 'DEBIT_CARD')
        
        # Validaciones
        self.assertEqual(paid_order.state, OrderState.CONFIRMED)
        self.assertEqual(paid_order.id, self.pending_order.id)

    def test_18_order_service_refund_order(self):
        """
        Test 18: Probar OrderService.refund_order.
        Valida que el servicio funciona correctamente.
        """
        # Usar el servicio para reembolsar
        refunded_order = OrderService.refund_order(self.confirmed_order.id, self.user.id)
        
        # Validaciones
        self.assertEqual(refunded_order.state, OrderState.REFUNDED)
        self.assertEqual(refunded_order.id, self.confirmed_order.id)

    def test_19_state_transition_flow(self):
        """
        Test 19: Flujo completo de transiciones de estado.
        PENDING -> CONFIRMED -> COMPLETED -> REFUNDED
        """
        # Crear nueva orden para el flujo
        flow_order = Orders.objects.create(
            user=self.user,
            date=timezone.now(),
            state=OrderState.PENDING,
            total=Decimal('500.00'),
            idempotency_key='test-flow'
        )
        
        # PENDING -> CONFIRMED
        confirmed_order = pay_order(flow_order.id, self.user.id, 'CREDIT_CARD')
        self.assertEqual(confirmed_order.state, OrderState.CONFIRMED)
        
        # CONFIRMED -> COMPLETED (simular manualmente)
        confirmed_order.state = OrderState.COMPLETED
        confirmed_order.save()
        
        # COMPLETED -> REFUNDED
        refunded_order = refund_order(confirmed_order.id, self.user.id)
        self.assertEqual(refunded_order.state, OrderState.REFUNDED)

    def test_20_invalid_state_transitions(self):
        """
        Test 20: Validar transiciones de estado inválidas.
        """
        # PENDING -> REFUNDED (inválido)
        with self.assertRaises(Exception):
            refund_order(self.pending_order.id, self.user.id)
        
        # CONFIRMED -> PENDING (inválido - no hay función para esto)
        # COMPLETED -> CONFIRMED (inválido - no hay función para esto)
        # REFUNDED -> CONFIRMED (inválido - no hay función para esto) 