from ninja import Router
from ninja.pagination import LimitOffsetPagination, paginate
from typing import List, Optional
from datetime import datetime, date
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.db.models import Q

from api.products.models import StockAuditLog, StockChangeHistory, StockMetrics
from api.products.services.audit_services import StockAuditQueryService
from api.products.schemas import (
    AuditLogOut, StockChangeOut, StockMetricsOut, 
    OperationSummaryOut
)

audit_router = Router(tags=["Audit"])


@audit_router.get("/audit/logs/", response=List[AuditLogOut])
@paginate(LimitOffsetPagination)
def list_audit_logs(
    request: HttpRequest,
    product_type: Optional[str] = None,
    product_id: Optional[int] = None,
    operation_type: Optional[str] = None,
    user_id: Optional[int] = None,
    success_only: bool = False,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    ordering: Optional[str] = None
):
    """
    Lista logs de auditoría con filtros y paginación.
    """
    queryset = StockAuditLog.objects.all()
    
    # Aplicar filtros
    if product_type:
        queryset = queryset.filter(product_type=product_type)
    
    if product_id:
        queryset = queryset.filter(product_id=product_id)
    
    if operation_type:
        queryset = queryset.filter(operation_type=operation_type)
    
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    if success_only:
        queryset = queryset.filter(success=True)
    
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date)
    
    if search:
        queryset = queryset.filter(
            Q(operation_type__icontains=search) |
            Q(product_type__icontains=search) |
            Q(error_message__icontains=search)
        )
    
    # Aplicar ordenamiento
    if ordering:
        queryset = queryset.order_by(ordering)
    else:
        queryset = queryset.order_by('-created_at')
    
    return queryset


@audit_router.get("/audit/logs/{log_id}/", response=AuditLogOut)
def get_audit_log_detail(request: HttpRequest, log_id: int):
    """
    Obtiene el detalle de un log de auditoría específico.
    """
    audit_log = get_object_or_404(StockAuditLog, id=log_id)
    return audit_log


@audit_router.get("/audit/logs/{log_id}/changes/", response=List[StockChangeOut])
@paginate(LimitOffsetPagination)
def list_stock_changes(
    request: HttpRequest,
    log_id: int,
    field_name: Optional[str] = None,
    change_type: Optional[str] = None,
    ordering: Optional[str] = None
):
    """
    Lista cambios de stock para un log específico.
    """
    # Verificar que el log existe
    get_object_or_404(StockAuditLog, id=log_id)
    
    queryset = StockChangeHistory.objects.filter(audit_log_id=log_id)
    
    # Aplicar filtros
    if field_name:
        queryset = queryset.filter(field_name=field_name)
    
    if change_type:
        queryset = queryset.filter(change_type=change_type)
    
    # Aplicar ordenamiento
    if ordering:
        queryset = queryset.order_by(ordering)
    else:
        queryset = queryset.order_by('-created_at')
    
    return queryset


@audit_router.get("/audit/metrics/", response=List[StockMetricsOut])
@paginate(LimitOffsetPagination)
def list_stock_metrics(
    request: HttpRequest,
    product_type: Optional[str] = None,
    product_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    ordering: Optional[str] = None
):
    """
    Lista métricas de stock con filtros y paginación.
    """
    queryset = StockMetrics.objects.all()
    
    # Aplicar filtros
    if product_type:
        queryset = queryset.filter(product_type=product_type)
    
    if product_id:
        queryset = queryset.filter(product_id=product_id)
    
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    
    # Aplicar ordenamiento
    if ordering:
        queryset = queryset.order_by(ordering)
    else:
        queryset = queryset.order_by('-date', '-created_at')
    
    return queryset


@audit_router.get("/audit/metrics/{metric_id}/", response=StockMetricsOut)
def get_stock_metrics_detail(request: HttpRequest, metric_id: int):
    """
    Obtiene el detalle de una métrica de stock específica.
    """
    metric = get_object_or_404(StockMetrics, id=metric_id)
    return metric


@audit_router.get("/audit/summary/", response=OperationSummaryOut)
def get_operation_summary(
    request: HttpRequest,
    product_type: Optional[str] = None,
    product_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Obtiene un resumen de operaciones de stock.
    """
    summary = StockAuditQueryService.get_operation_summary(
        product_type=product_type,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return summary 