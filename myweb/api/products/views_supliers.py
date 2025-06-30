# views_suppliers.py
from ninja import Router
from .models import Suppliers
from .schemas import SupplierOut, SupplierCreate, SupplierUpdate
from typing import List
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from django.db.models import Q
from django.utils import timezone

suppliers_router = Router(tags=["Suppliers"])

@suppliers_router.get("/", response=List[SupplierOut])
def listar_suppliers(request):
    """
    Lista todos los proveedores activos (no eliminados lógicamente)
    """
    return Suppliers.objects.filter(deleted_at__isnull=True)

@suppliers_router.get("/{id}/", response=SupplierOut)
def obtener_supplier(request, id: int):
    """
    Obtiene un proveedor específico por su ID
    """
    return get_object_or_404(Suppliers, id=id, deleted_at__isnull=True)

@suppliers_router.post("/", response=SupplierOut)
def crear_supplier(request, data: SupplierCreate):
    """
    Crea un nuevo proveedor con validación de duplicados
    """
    # Validación de duplicados por email u organización
    if Suppliers.objects.filter(
        Q(email=data.email) | Q(organization_name=data.organization_name),
        deleted_at__isnull=True
    ).exists():
        raise HttpError(400, "Ya existe un proveedor con el mismo email o nombre de organización.")
    
    return Suppliers.objects.create(**data.dict())

@suppliers_router.patch("/{id}/", response=SupplierOut)
def actualizar_supplier(request, id: int, data: SupplierUpdate):
    """
    Actualiza un proveedor existente (solo campos proporcionados)
    """
    supplier = get_object_or_404(Suppliers, id=id, deleted_at__isnull=True)
    
    # Validación de duplicados solo si se está actualizando email u organización
    update_data = data.dict(exclude_unset=True)
    if 'email' in update_data or 'organization_name' in update_data:
        duplicate_query = Q()
        if 'email' in update_data:
            duplicate_query |= Q(email=update_data['email'])
        if 'organization_name' in update_data:
            duplicate_query |= Q(organization_name=update_data['organization_name'])
        
        if Suppliers.objects.filter(duplicate_query, deleted_at__isnull=True).exclude(id=id).exists():
            raise HttpError(400, "Ya existe otro proveedor con el mismo email o nombre de organización.")
    
    for field, value in update_data.items():
        setattr(supplier, field, value)
    supplier.save()
    return supplier

@suppliers_router.delete("/{id}/", response={204: None})
def eliminar_supplier(request, id: int):
    """
    Elimina lógicamente un proveedor (marca como eliminado sin borrar de BD)
    """
    supplier = get_object_or_404(Suppliers, id=id, deleted_at__isnull=True)
    supplier.deleted_at = timezone.now()
    supplier.save()
    return 204, None

@suppliers_router.get("/eliminados/", response=List[SupplierOut])
def listar_suppliers_eliminados(request):
    """
    Lista todos los proveedores eliminados lógicamente (para administración)
    """
    return Suppliers.objects.filter(deleted_at__isnull=False)

@suppliers_router.patch("/{id}/restaurar/", response=SupplierOut)
def restaurar_supplier(request, id: int):
    """
    Restaura un proveedor eliminado lógicamente
    """
    supplier = get_object_or_404(Suppliers, id=id, deleted_at__isnull=False)
    supplier.deleted_at = None
    supplier.save()
    return supplier
