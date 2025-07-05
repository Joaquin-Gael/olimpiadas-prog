import logging
import uuid
from datetime import datetime, date
from django.utils import timezone
from django.db import transaction, models
from typing import Optional, Dict, Any, List
from api.products.models import StockAuditLog, StockChangeHistory, StockMetrics

logger = logging.getLogger(__name__)


class StockAuditService:
    """
    Servicio para manejar la auditoría y logs de todas las operaciones de stock.
    Proporciona métodos para registrar operaciones, cambios y métricas.
    """
    
    @staticmethod
    def get_request_context(request=None) -> Dict[str, Any]:
        """
        Extrae información del contexto de la solicitud para auditoría.
        """
        context = {
            'user_id': None,
            'session_id': None,
            'request_id': str(uuid.uuid4()),
        }
        
        if request:
            # Extraer user_id si está disponible
            if hasattr(request, 'user') and request.user.is_authenticated:
                context['user_id'] = request.user.id
            
            # Extraer session_id si está disponible
            if hasattr(request, 'session') and request.session.session_key:
                context['session_id'] = request.session.session_key
            
            # Usar request_id existente si está disponible
            if hasattr(request, 'request_id'):
                context['request_id'] = request.request_id
        
        return context
    
    @staticmethod
    def log_stock_operation(
        operation_type: str,
        product_type: str,
        product_id: int,
        quantity: int,
        previous_stock: Optional[int] = None,
        new_stock: Optional[int] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: str = ""
    ) -> StockAuditLog:
        """
        Registra una operación de stock en el sistema de auditoría.
        """
        try:
            audit_log = StockAuditLog.log_operation(
                operation_type=operation_type,
                product_type=product_type,
                product_id=product_id,
                quantity=quantity,
                previous_stock=previous_stock,
                new_stock=new_stock,
                user_id=user_id,
                session_id=session_id,
                request_id=request_id,
                metadata=metadata or {},
                success=success,
                error_message=error_message
            )
            
            logger.info(
                f"Stock operation logged: {operation_type} {product_type} {product_id} "
                f"quantity={quantity} success={success}"
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Error logging stock operation: {e}")
            # No lanzar excepción para no interrumpir la operación principal
            return None
    
    @staticmethod
    def log_stock_change(
        audit_log: StockAuditLog,
        field_name: str,
        old_value: Optional[int],
        new_value: Optional[int]
    ) -> StockChangeHistory:
        """
        Registra un cambio específico en un campo de stock.
        """
        try:
            if old_value == new_value:
                return None  # No registrar cambios sin diferencia
            
            change_type = "set"
            if old_value is not None and new_value is not None:
                if new_value > old_value:
                    change_type = "increase"
                elif new_value < old_value:
                    change_type = "decrease"
            
            change_history = StockChangeHistory.log_change(
                audit_log=audit_log,
                change_type=change_type,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value
            )
            
            logger.debug(
                f"Stock change logged: {field_name} {old_value} -> {new_value} "
                f"({change_type})"
            )
            
            return change_history
            
        except Exception as e:
            logger.error(f"Error logging stock change: {e}")
            return None
    
    @staticmethod
    def update_stock_metrics(
        product_type: str,
        product_id: int,
        total_capacity: int,
        current_reserved: int,
        current_available: int,
        as_of_date: Optional[date] = None
    ) -> StockMetrics:
        """
        Actualiza las métricas de stock para análisis y reportes.
        """
        try:
            # Obtener o crear métricas
            metrics, created = StockMetrics.objects.get_or_create(
                product_type=product_type,
                product_id=product_id,
                date=as_of_date or timezone.now().date(),
                defaults={
                    'total_capacity': total_capacity,
                    'current_reserved': current_reserved,
                    'current_available': current_available,
                    'utilization_rate': (current_reserved / total_capacity * 100) if total_capacity > 0 else 0,
                    'total_reservations': 0,
                    'total_releases': 0,
                    'failed_operations': 0
                }
            )
            
            if not created:
                # Actualizar métricas existentes
                metrics.total_capacity = total_capacity
                metrics.current_reserved = current_reserved
                metrics.current_available = current_available
                metrics.utilization_rate = (current_reserved / total_capacity * 100) if total_capacity > 0 else 0
            
            # Calcular contadores desde los logs
            logs = StockAuditLog.objects.filter(
                product_type=product_type,
                product_id=product_id
            )
            
            # Contar reservas exitosas
            metrics.total_reservations = logs.filter(
                operation_type="reserve",
                success=True
            ).count()
            
            # Contar liberaciones exitosas
            metrics.total_releases = logs.filter(
                operation_type="release",
                success=True
            ).count()
            
            # Contar operaciones fallidas
            metrics.failed_operations = logs.filter(
                success=False
            ).count()
            
            metrics.save()
            
            logger.debug(
                f"Stock metrics updated: {product_type} {product_id} "
                f"utilization={metrics.utilization_rate}% "
                f"reservations={metrics.total_reservations} "
                f"releases={metrics.total_releases} "
                f"failed={metrics.failed_operations}"
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error updating stock metrics: {e}")
            return None
    
    @staticmethod
    def log_activity_stock_operation(
        operation_type: str,
        availability_id: int,
        quantity: int,
        previous_reserved: Optional[int] = None,
        new_reserved: Optional[int] = None,
        request=None,
        success: bool = True,
        error_message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> StockAuditLog:
        """
        Registra una operación específica de stock de actividad.
        """
        context = StockAuditService.get_request_context(request)
        
        audit_log = StockAuditService.log_stock_operation(
            operation_type=operation_type,
            product_type="activity",
            product_id=availability_id,
            quantity=quantity,
            previous_stock=previous_reserved,
            new_stock=new_reserved,
            user_id=context['user_id'],
            session_id=context['session_id'],
            request_id=context['request_id'],
            metadata=metadata,
            success=success,
            error_message=error_message
        )
        
        if audit_log and previous_reserved != new_reserved:
            StockAuditService.log_stock_change(
                audit_log=audit_log,
                field_name="reserved_seats",
                old_value=previous_reserved,
                new_value=new_reserved
            )
        
        return audit_log
    
    @staticmethod
    def log_transportation_stock_operation(
        operation_type: str,
        availability_id: int,
        quantity: int,
        previous_reserved: Optional[int] = None,
        new_reserved: Optional[int] = None,
        request=None,
        success: bool = True,
        error_message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> StockAuditLog:
        """
        Registra una operación específica de stock de transporte.
        """
        context = StockAuditService.get_request_context(request)
        
        audit_log = StockAuditService.log_stock_operation(
            operation_type=operation_type,
            product_type="transportation",
            product_id=availability_id,
            quantity=quantity,
            previous_stock=previous_reserved,
            new_stock=new_reserved,
            user_id=context['user_id'],
            session_id=context['session_id'],
            request_id=context['request_id'],
            metadata=metadata,
            success=success,
            error_message=error_message
        )
        
        if audit_log and previous_reserved != new_reserved:
            StockAuditService.log_stock_change(
                audit_log=audit_log,
                field_name="reserved_seats",
                old_value=previous_reserved,
                new_value=new_reserved
            )
        
        return audit_log
    
    @staticmethod
    def log_room_stock_operation(
        operation_type: str,
        availability_id: int,
        quantity: int,
        previous_available: Optional[int] = None,
        new_available: Optional[int] = None,
        request=None,
        success: bool = True,
        error_message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> StockAuditLog:
        """
        Registra una operación específica de stock de habitaciones.
        """
        context = StockAuditService.get_request_context(request)
        
        audit_log = StockAuditService.log_stock_operation(
            operation_type=operation_type,
            product_type="room",
            product_id=availability_id,
            quantity=quantity,
            previous_stock=previous_available,
            new_stock=new_available,
            user_id=context['user_id'],
            session_id=context['session_id'],
            request_id=context['request_id'],
            metadata=metadata,
            success=success,
            error_message=error_message
        )
        
        if audit_log and previous_available != new_available:
            StockAuditService.log_stock_change(
                audit_log=audit_log,
                field_name="available_quantity",
                old_value=previous_available,
                new_value=new_available
            )
        
        return audit_log
    
    @staticmethod
    def log_flight_stock_operation(
        operation_type: str,
        flight_id: int,
        quantity: int,
        previous_available: Optional[int] = None,
        new_available: Optional[int] = None,
        request=None,
        success: bool = True,
        error_message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> StockAuditLog:
        """
        Registra una operación específica de stock de vuelos.
        """
        context = StockAuditService.get_request_context(request)
        
        audit_log = StockAuditService.log_stock_operation(
            operation_type=operation_type,
            product_type="flight",
            product_id=flight_id,
            quantity=quantity,
            previous_stock=previous_available,
            new_stock=new_available,
            user_id=context['user_id'],
            session_id=context['session_id'],
            request_id=context['request_id'],
            metadata=metadata,
            success=success,
            error_message=error_message
        )
        
        if audit_log and previous_available != new_available:
            StockAuditService.log_stock_change(
                audit_log=audit_log,
                field_name="available_seats",
                old_value=previous_available,
                new_value=new_available
            )
        
        return audit_log


class StockAuditQueryService:
    """
    Servicio para consultar y analizar los logs de auditoría de stock.
    """
    
    @staticmethod
    def get_audit_logs(
        product_type: Optional[str] = None,
        product_id: Optional[int] = None,
        operation_type: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success_only: bool = False,
        limit: int = 100
    ) -> List[StockAuditLog]:
        """
        Obtiene logs de auditoría con filtros opcionales.
        """
        queryset = StockAuditLog.objects.all()
        
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        if success_only:
            queryset = queryset.filter(success=True)
        
        return list(queryset[:limit])
    
    @staticmethod
    def get_stock_changes(
        audit_log_id: Optional[int] = None,
        product_type: Optional[str] = None,
        product_id: Optional[int] = None,
        field_name: Optional[str] = None,
        change_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[StockChangeHistory]:
        """
        Obtiene cambios específicos de stock con filtros opcionales.
        """
        queryset = StockChangeHistory.objects.select_related('audit_log')
        
        if audit_log_id:
            queryset = queryset.filter(audit_log_id=audit_log_id)
        
        if product_type:
            queryset = queryset.filter(audit_log__product_type=product_type)
        
        if product_id:
            queryset = queryset.filter(audit_log__product_id=product_id)
        
        if field_name:
            queryset = queryset.filter(field_name=field_name)
        
        if change_type:
            queryset = queryset.filter(change_type=change_type)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return list(queryset[:limit])
    
    @staticmethod
    def get_stock_metrics(
        product_type: Optional[str] = None,
        product_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[StockMetrics]:
        """
        Obtiene métricas de stock con filtros opcionales.
        """
        queryset = StockMetrics.objects.all()
        
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return list(queryset[:limit])
    
    @staticmethod
    def get_operation_summary(
        product_type: Optional[str] = None,
        product_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene un resumen de operaciones de stock.
        """
        queryset = StockAuditLog.objects.all()
        
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        total_operations = queryset.count()
        successful_operations = queryset.filter(success=True).count()
        failed_operations = total_operations - successful_operations
        
        operation_types = queryset.values('operation_type').annotate(
            count=models.Count('id')
        )
        
        return {
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'failed_operations': failed_operations,
            'success_rate': (successful_operations / total_operations * 100) if total_operations > 0 else 0,
            'operation_types': list(operation_types)
        } 