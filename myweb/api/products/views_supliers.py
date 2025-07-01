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
def list_suppliers(request):
    """
    Lists all active suppliers (not logically deleted)
    """
    return Suppliers.objects.filter(deleted_at__isnull=True)

@suppliers_router.get("/{id}/", response=SupplierOut)
def get_supplier(request, id: int):
    """
    Gets a specific supplier by its ID
    """
    return get_object_or_404(Suppliers, id=id, deleted_at__isnull=True)

@suppliers_router.post("/", response=SupplierOut)
def create_supplier(request, data: SupplierCreate):
    """
    Creates a new supplier with duplicate validation
    """
    # Duplicate validation by email or organization name
    if Suppliers.objects.filter(
        Q(email=data.email) | Q(organization_name=data.organization_name),
        deleted_at__isnull=True
    ).exists():
        raise HttpError(400, "A supplier with the same email or organization name already exists.")
    
    return Suppliers.objects.create(**data.dict())

@suppliers_router.patch("/{id}/", response=SupplierOut)
def update_supplier(request, id: int, data: SupplierUpdate):
    """
    Updates an existing supplier (only provided fields)
    """
    supplier = get_object_or_404(Suppliers, id=id, deleted_at__isnull=True)
    
    # Duplicate validation only if updating email or organization name
    update_data = data.dict(exclude_unset=True)
    if 'email' in update_data or 'organization_name' in update_data:
        duplicate_query = Q()
        if 'email' in update_data:
            duplicate_query |= Q(email=update_data['email'])
        if 'organization_name' in update_data:
            duplicate_query |= Q(organization_name=update_data['organization_name'])
        
        if Suppliers.objects.filter(duplicate_query, deleted_at__isnull=True).exclude(id=id).exists():
            raise HttpError(400, "Another supplier with the same email or organization name already exists.")
    
    for field, value in update_data.items():
        setattr(supplier, field, value)
    supplier.save()
    return supplier

@suppliers_router.delete("/{id}/", response={204: None})
def delete_supplier(request, id: int):
    """
    Logically deletes a supplier (marks as deleted without removing from DB)
    """
    supplier = get_object_or_404(Suppliers, id=id, deleted_at__isnull=True)
    supplier.deleted_at = timezone.now()
    supplier.save()
    return 204, None

@suppliers_router.get("/deleted/", response=List[SupplierOut])
def list_deleted_suppliers(request):
    """
    Lists all logically deleted suppliers (for administration)
    """
    return Suppliers.objects.filter(deleted_at__isnull=False)

@suppliers_router.patch("/{id}/restore/", response=SupplierOut)
def restore_supplier(request, id: int):
    """
    Restores a logically deleted supplier
    """
    supplier = get_object_or_404(Suppliers, id=id, deleted_at__isnull=False)
    supplier.deleted_at = None
    supplier.save()
    return supplier
