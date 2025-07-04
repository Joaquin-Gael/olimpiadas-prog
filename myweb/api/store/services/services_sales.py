"""
Servicios para manejo de ventas
"""
from decimal import Decimal
from typing import List, Optional, Dict, Any
from django.db import transaction
from django.db.models import Sum, Count
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import Sale, Order
from ..idempotency import check_idempotency


class SalesService:
    """Servicio para manejo de ventas"""
    
    @staticmethod
    @check_idempotency
    def create_sale(
        order_id: int,
        amount: Decimal,
        payment_method: str,
        transaction_id: str,
        idempotency_key: str,
        **kwargs
    ) -> Sale:
        """
        Crea una nueva venta
        
        Args:
            order_id: ID de la orden
            amount: Monto de la venta
            payment_method: Método de pago
            transaction_id: ID de la transacción
            idempotency_key: Clave de idempotencia
            **kwargs: Campos adicionales
            
        Returns:
            Sale: La venta creada
        """
        with transaction.atomic():
            # Verificar que la orden existe y está en estado válido
            try:
                order = Order.objects.select_for_update().get(
                    id=order_id,
                    state__in=[Order.State.PENDING, Order.State.CONFIRMED]
                )
            except Order.DoesNotExist:
                raise ValidationError("Orden no encontrada o no válida para venta")
            
            # Verificar que no exista ya una venta para esta orden
            if Sale.objects.filter(order=order).exists():
                raise ValidationError("Ya existe una venta para esta orden")
            
            # Crear la venta
            sale = Sale.objects.create(
                order=order,
                amount=amount,
                payment_method=payment_method,
                payment_status=Sale.PaymentStatus.PAID_ONLINE,
                transaction_id=transaction_id,
                idempotency_key=idempotency_key,
                **kwargs
            )
            
            # Actualizar estado de la orden si está pendiente
            if order.state == Order.State.PENDING:
                order.state = Order.State.CONFIRMED
                order.save()
            
            return sale
    
    @staticmethod
    def get_sale_by_id(sale_id: int) -> Optional[Sale]:
        """
        Obtiene una venta por ID
        
        Args:
            sale_id: ID de la venta
            
        Returns:
            Sale: La venta o None si no existe
        """
        try:
            return Sale.objects.select_related('order', 'order__user').get(id=sale_id)
        except Sale.DoesNotExist:
            return None
    
    @staticmethod
    def get_sales_by_user(user_id: int, limit: int = 50) -> List[Sale]:
        """
        Obtiene las ventas de un usuario
        
        Args:
            user_id: ID del usuario
            limit: Límite de resultados
            
        Returns:
            List[Sale]: Lista de ventas
        """
        return list(Sale.objects.filter(
            order__user_id=user_id
        ).select_related(
            'order', 'order__user'
        ).order_by('-created_at')[:limit])
    
    @staticmethod
    def get_sales_summary(user_id: int) -> Dict[str, Any]:
        """
        Obtiene un resumen de ventas de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con estadísticas de ventas
        """
        sales = Sale.objects.filter(
            order__user_id=user_id,
            payment_status=Sale.PaymentStatus.PAID_ONLINE
        )
        
        total_sales = sales.count()
        total_amount = sales.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Ventas del último mes
        last_month = timezone.now() - timezone.timedelta(days=30)
        recent_sales = sales.filter(created_at__gte=last_month)
        recent_count = recent_sales.count()
        recent_amount = recent_sales.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        return {
            'total_sales': total_sales,
            'total_amount': total_amount,
            'recent_sales_count': recent_count,
            'recent_sales_amount': recent_amount,
            'average_amount': total_amount / total_sales if total_sales > 0 else Decimal('0.00')
        }
    
    @staticmethod
    def update_sale_status(
        sale_id: int,
        new_status: Sale.PaymentStatus
    ) -> Sale:
        """
        Actualiza el estado de pago de una venta
        
        Args:
            sale_id: ID de la venta
            new_status: Nuevo estado de pago
            
        Returns:
            Sale: La venta actualizada
        """
        with transaction.atomic():
            sale = Sale.objects.select_for_update().get(id=sale_id)
            sale.payment_status = new_status
            sale.save()
            
            # Actualizar estado de la orden si es necesario
            if new_status == Sale.PaymentStatus.REFUNDED:
                sale.order.state = Order.State.REFUNDED
                sale.order.save()
            
            return sale
    
    @staticmethod
    def get_sales_by_date_range(
        start_date: timezone.datetime,
        end_date: timezone.datetime,
        user_id: Optional[int] = None
    ) -> List[Sale]:
        """
        Obtiene ventas en un rango de fechas
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            user_id: ID del usuario (opcional)
            
        Returns:
            List[Sale]: Lista de ventas
        """
        queryset = Sale.objects.filter(
            created_at__range=(start_date, end_date)
        ).select_related('order', 'order__user')
        
        if user_id:
            queryset = queryset.filter(order__user_id=user_id)
        
        return list(queryset.order_by('-created_at'))
    
    @staticmethod
    def get_sales_statistics(
        start_date: Optional[timezone.datetime] = None,
        end_date: Optional[timezone.datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de ventas
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            
        Returns:
            Dict con estadísticas
        """
        queryset = Sale.objects.filter(
            payment_status=Sale.PaymentStatus.PAID_ONLINE
        )
        
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=(start_date, end_date))
        
        total_sales = queryset.count()
        total_amount = queryset.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Métodos de pago más populares
        payment_methods = queryset.values('payment_method').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return {
            'total_sales': total_sales,
            'total_amount': total_amount,
            'average_amount': total_amount / total_sales if total_sales > 0 else Decimal('0.00'),
            'payment_methods': list(payment_methods)
        } 