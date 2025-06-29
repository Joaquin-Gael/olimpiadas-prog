# views_suppliers.py
from ninja import Router
from .models import Suppliers
from .schemas import SupplierOut, SupplierCreate, SupplierUpdate
from typing import List
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

suppliers_router = Router(tags=["Suppliers"])

@suppliers_router.get("/", response=List[SupplierOut])
def listar_suppliers(request):
    return Suppliers.objects.all()

@suppliers_router.get("/{id}/", response=SupplierOut)
def obtener_supplier(request, id: int):
    return get_object_or_404(Suppliers, id=id)

@suppliers_router.post("/", response=SupplierOut)
def crear_supplier(request, data: SupplierCreate):
    supplier = Suppliers.objects.create(**data.dict())
    return supplier

@suppliers_router.patch("/{id}/", response=SupplierOut)
def actualizar_supplier(request, id: int, data: SupplierUpdate):
    supplier = get_object_or_404(Suppliers, id=id)
    for field, value in data.dict(exclude_unset=True).items():
        setattr(supplier, field, value)
    supplier.save()
    return supplier

@suppliers_router.delete("/{id}/", response={204: None})
def eliminar_supplier(request, id: int):
    supplier = get_object_or_404(Suppliers, id=id)
    supplier.delete()
    return 204, None
