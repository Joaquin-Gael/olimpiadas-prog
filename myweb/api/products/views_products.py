from ninja import Router
from .schemas import ProductsMetadataOut, ProductsMetadataCreate, ProductsMetadataUpdate
from .helpers import serialize_product_metadata
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from .models import (
    ProductsMetadata, Suppliers,
    Activities, Flights, Lodgments, Transportation
)
from django.db.models import Q
from ninja.pagination import paginate
from .filters import ProductosFiltro
from .pagination import DefaultPagination
from django.db import transaction
from django.utils import timezone
from datetime import datetime

products_router = Router(tags=["Productos"]) 

@products_router.post("/productos/crear/", response=ProductsMetadataOut)
def crear_producto(request, data: ProductsMetadataCreate):
    supplier = get_object_or_404(Suppliers, id=data.supplier_id)

    tipo = data.tipo_producto
    producto_creado = None

    # Crear el producto correspondiente
    if tipo == "actividad":
        producto_creado = Activities.objects.create(**data.producto.dict())
    elif tipo == "vuelo":
        producto_creado = Flights.objects.create(**data.producto.dict())
    elif tipo == "alojamiento":
        producto_creado = Lodgments.objects.create(**data.producto.dict())
    elif tipo == "transporte":
        producto_creado = Transportation.objects.create(**data.producto.dict())
    else:
        raise HttpError(400, "Tipo de producto no válido")

    # Crear metadata relacionada
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_object=producto_creado,
        tipo_producto=tipo,
        precio_unitario=data.precio_unitario
    )

    # Devolver schema serializado
    return serialize_product_metadata(metadata)

@products_router.get("/productos/", response=list[ProductsMetadataOut])
@paginate(DefaultPagination)
def listar_productos(request, filtros: ProductosFiltro = ProductosFiltro()):
    qs = (
        ProductsMetadata.active      # <-- Solo productos activos
        .select_related("content_type")
    )

    # --- filtros por campo directo ---
    if filtros.tipo:
        qs = qs.filter(tipo_producto=filtros.tipo)
    if filtros.precio_min is not None:
        qs = qs.filter(precio_unitario__gte=filtros.precio_min)
    if filtros.precio_max is not None:
        qs = qs.filter(precio_unitario__lte=filtros.precio_max)
    if filtros.supplier_id:
        qs = qs.filter(supplier_id=filtros.supplier_id)

    # --- filtros que dependen del modelo real ---
    if filtros.destino_id:
        qs = qs.filter(
            Q(flights__destination_id=filtros.destino_id) |
            Q(transportation__destination_id=filtros.destino_id) |
            Q(lodgment__location_id=filtros.destino_id) |
            Q(activity__location_id=filtros.destino_id)
        )
    if filtros.origen_id:
        qs = qs.filter(
            Q(flights__origin_id=filtros.origen_id) |
            Q(transportation__origin_id=filtros.origen_id)
        )

    if filtros.fecha_min:
        qs = qs.filter(
            Q(activity__date__gte=filtros.fecha_min) |
            Q(flights__departure_date__gte=filtros.fecha_min) |
            Q(transportation__departure_date__gte=filtros.fecha_min) |
            Q(lodgment__date_checkin__gte=filtros.fecha_min)
        )
    if filtros.fecha_max:
        qs = qs.filter(
            Q(activity__date__lte=filtros.fecha_max) |
            Q(flights__departure_date__lte=filtros.fecha_max) |
            Q(transportation__departure_date__lte=filtros.fecha_max) |
            Q(lodgment__date_checkin__lte=filtros.fecha_max)
        )

    if filtros.search:
        qs = qs.filter(
            Q(activity__name__icontains=filtros.search) |
            Q(activity__description__icontains=filtros.search) |
            Q(flights__airline__icontains=filtros.search) |
            Q(lodgment__name__icontains=filtros.search) |
            Q(transportation__description__icontains=filtros.search)
        )

    # --- orden ---
    if filtros.ordering:
        # mapa de alias → campo real
        order_map = {
            "precio": "precio_unitario",
            "-precio": "-precio_unitario",
            "fecha": "activity__date",
            "-fecha": "-activity__date",
        }
        qs = qs.order_by(order_map.get(filtros.ordering, "precio_unitario"))

    # Devolvemos queryset paginado; Ninja llamará a serialize_product_metadata para cada item
    return [serialize_product_metadata(p) for p in qs]



@products_router.get("/productos/{id}/", response=ProductsMetadataOut)
def obtener_producto(request, id: int):
    metadata = get_object_or_404(ProductsMetadata.active.select_related("content_type"), id=id)
    return serialize_product_metadata(metadata)

@products_router.patch("/producto/{id}/", response=ProductsMetadataOut)
@transaction.atomic
def actualizar_producto(request, id: int, data: ProductsMetadataUpdate):
    metadata = get_object_or_404(
        ProductsMetadata.objects.select_related("content_type"), id=id
    )

    # --- reglas: tipo_producto NO cambia ---
    if data.producto and metadata.tipo_producto != data.producto.__class__.__name__.lower():
        raise HttpError(422, "No se puede cambiar el tipo de producto")

    # --- actualizar precio y proveedor si se envían ---
    if data.precio_unitario is not None:
        if data.precio_unitario < 0:
            raise HttpError(400, "El precio no puede ser negativo")
        metadata.precio_unitario = data.precio_unitario

    if data.supplier_id is not None:
        metadata.supplier_id = data.supplier_id

    # --- actualizar campos del objeto real ---
    if data.producto is not None:
        producto = metadata.content          # instancia concreta
        for attr, value in data.producto.dict(exclude_unset=True).items():
            setattr(producto, attr, value)
        producto.full_clean()                # valida reglas de modelo
        producto.save(update_fields=list(data.producto.dict(exclude_unset=True).keys()))

    metadata.save(update_fields=["precio_unitario", "supplier_id"])

    return serialize_product_metadata(metadata)

@products_router.delete("/producto/{id}/", response={204: None})
@transaction.atomic
def inactivar_producto(request, id: int):
    metadata = get_object_or_404(ProductsMetadata, id=id)

    # Regla: si el producto tiene ventas confirmadas ⇒ sólo se inactiva
    if metadata.orders.exists():             # su nombre real del related_name
        metadata.is_active  = False
        metadata.deleted_at = timezone.now()
        metadata.save(update_fields=["is_active", "deleted_at"])
    else:
        # Producto nunca vendido → inactiva metadata y sub-modelo
        metadata.is_active  = False
        metadata.deleted_at = timezone.now()
        metadata.save(update_fields=["is_active", "deleted_at"])
        metadata.content.is_active = False   # si el sub-modelo también lo tiene
        metadata.content.save(update_fields=["is_active"])

    return 204, None

    