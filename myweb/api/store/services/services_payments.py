"""
Servicios para manejo de pagos
"""
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional
from django.db import transaction
from django.core.exceptions import ValidationError

from ..models import Order, Sale
from ..idempotency import check_idempotency


class PaymentService:
    """Servicio para manejo de pagos"""
    
    @staticmethod
    @check_idempotency
    def process_payment(
        order_id: int,
        payment_method: str,
        payment_data: Dict[str, Any],
        idempotency_key: str
    ) -> Sale:
        """
        Procesa el pago de una orden
        
        Args:
            order_id: ID de la orden
            payment_method: Método de pago (credit_card, debit_card, etc.)
            payment_data: Datos del pago (tarjeta, etc.)
            idempotency_key: Clave de idempotencia
            
        Returns:
            Sale: La venta creada
            
        Raises:
            ValidationError: Si el pago falla
        """
        with transaction.atomic():
            # Obtener la orden
            try:
                order = Order.objects.select_for_update().get(
                    id=order_id,
                    state=Order.State.PENDING
                )
            except Order.DoesNotExist:
                raise ValidationError("Orden no encontrada o no válida para pago")
            
            # Simular procesamiento de pago
            payment_result = PaymentService._process_payment_with_gateway(
                order.total,
                payment_method,
                payment_data
            )
            
            if not payment_result['success']:
                raise ValidationError(f"Pago rechazado: {payment_result['message']}")
            
            # Crear la venta
            sale = Sale.objects.create(
                order=order,
                amount=order.total,
                payment_method=payment_method,
                payment_status=Sale.PaymentStatus.PAID_ONLINE,
                transaction_id=payment_result['transaction_id'],
                idempotency_key=idempotency_key
            )
            
            # Actualizar estado de la orden
            order.state = Order.State.CONFIRMED
            order.save()
            
            return sale
    
    @staticmethod
    def _process_payment_with_gateway(
        amount: Decimal,
        payment_method: str,
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simula el procesamiento de pago con una pasarela externa
        
        Args:
            amount: Monto a cobrar
            payment_method: Método de pago
            payment_data: Datos del pago
            
        Returns:
            Dict con el resultado del pago
        """
        # Simulación de validaciones básicas
        if not payment_data.get('card_number'):
            return {
                'success': False,
                'message': 'Número de tarjeta requerido'
            }
        
        if not payment_data.get('expiry_date'):
            return {
                'success': False,
                'message': 'Fecha de vencimiento requerida'
            }
        
        if not payment_data.get('cvv'):
            return {
                'success': False,
                'message': 'CVV requerido'
            }
        
        # Simular rechazo por tarjetas que terminan en ciertos números
        card_number = payment_data['card_number']
        if card_number.endswith('0000'):
            return {
                'success': False,
                'message': 'Tarjeta rechazada por el banco'
            }
        
        if card_number.endswith('1111'):
            return {
                'success': False,
                'message': 'Fondos insuficientes'
            }
        
        # Simular éxito
        transaction_id = f"TXN_{uuid.uuid4().hex[:16].upper()}"
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'message': 'Pago procesado exitosamente'
        }
    
    @staticmethod
    def refund_payment(sale_id: int, amount: Optional[Decimal] = None) -> Sale:
        """
        Procesa un reembolso
        
        Args:
            sale_id: ID de la venta
            amount: Monto a reembolsar (si None, reembolsa todo)
            
        Returns:
            Sale: La venta actualizada
        """
        with transaction.atomic():
            try:
                sale = Sale.objects.select_for_update().get(
                    id=sale_id,
                    payment_status=Sale.PaymentStatus.PAID_ONLINE
                )
            except Sale.DoesNotExist:
                raise ValidationError("Venta no encontrada o no válida para reembolso")
            
            # Simular reembolso
            refund_result = PaymentService._process_refund_with_gateway(
                sale.transaction_id,
                amount or sale.amount
            )
            
            if not refund_result['success']:
                raise ValidationError(f"Reembolso rechazado: {refund_result['message']}")
            
            # Actualizar estado de la venta
            sale.payment_status = Sale.PaymentStatus.REFUNDED
            sale.save()
            
            # Actualizar estado de la orden
            sale.order.state = Order.State.REFUNDED
            sale.order.save()
            
            return sale
    
    @staticmethod
    def _process_refund_with_gateway(
        transaction_id: str,
        amount: Decimal
    ) -> Dict[str, Any]:
        """
        Simula el procesamiento de reembolso
        
        Args:
            transaction_id: ID de la transacción original
            amount: Monto a reembolsar
            
        Returns:
            Dict con el resultado del reembolso
        """
        # Simular éxito del reembolso
        return {
            'success': True,
            'refund_id': f"REF_{uuid.uuid4().hex[:16].upper()}",
            'message': 'Reembolso procesado exitosamente'
        }
    
    @staticmethod
    def get_payment_status(sale_id: int) -> Optional[Sale]:
        """
        Obtiene el estado de un pago
        
        Args:
            sale_id: ID de la venta
            
        Returns:
            Sale: La venta o None si no existe
        """
        try:
            return Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return None 