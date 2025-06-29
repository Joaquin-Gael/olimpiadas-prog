from ninja import Router
from .schemas import (
    ProductsMetadataOut, ProductsMetadataCreate, ProductsMetadataUpdate,
    ActivityUpdate, FlightUpdate, LodgmentUpdate, TransportationUpdate
)
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
from typing import List
from django.core.exceptions import ValidationError

products_router = Router(tags=["Products"])

# TODO: terminar de traducir todas las dependencias al ingles

@products_router.post("/create", response=ProductsMetadataOut)
@transaction.atomic
def create_product(request, data: ProductsMetadataCreate):
    """
    Create a new product and its metadata.

    Steps:
    1. Validate the supplier exists.
    2. Determine the actual product model from `product_type`.
    3. Instantiate and validate the domain object (`Activities`, `Flights`, etc.).
    4. Save the domain object to the database.
    5. Create a `ProductsMetadata` record linking supplier, pricing, and the newly created object.

    Returns the serialized metadata of the created product.
    Raises HTTP 400 if `product_type` is invalid or business validation fails.
    """
    supplier = get_object_or_404(Suppliers, id=data.supplier_id)

    # Map product_type to model class
    model_map = {
        "actividad": Activities,
        "vuelo": Flights,
        "alojamiento": Lodgments,
        "transporte": Transportation,
    }
    _model = model_map.get(data.product_type)
    if not _model:
        raise HttpError(400, "Invalid product_type provided.")

    # 1️⃣ Instantiate without saving
    product = _model(**data.product.dict())

    # 2️⃣ Perform full_clean() to enforce model validators and custom clean()
    try:
        product.full_clean()
    except Exception as e:
        raise HttpError(422, e.message_dict if hasattr(e, 'message_dict') else str(e))

    # 3️⃣ Save valid domain object
    product.save()

    # 4️⃣ Create metadata record
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_object=product,
        tipo_producto=data.product_type,
        precio_unitario=data.unit_price
    )

    return serialize_product_metadata(metadata)


@products_router.get("/", response=list[ProductsMetadataOut])
@paginate(DefaultPagination)
def list_products(request, filtros: ProductosFiltro = ProductosFiltro()):
    """
    List active products metadata with optional filters.

    Available filters:
    - tipo: filter by product type (actividad, vuelo, alojamiento, transporte)
    - precio_min, precio_max: filter by unit price range
    - supplier_id: filter by supplier
    - destino_id, origen_id: filter by destination or origin ID across related models
    - fecha_min, fecha_max: filter by date range on activities, flights, transportation, or lodging
    - search: full-text search on name/description fields
    - ordering: order by price or date (e.g., 'precio', '-fecha')

    Returns a paginated list of serialized product metadata.
    """
    qs = (
        ProductsMetadata.active
        .select_related("content_type")
        .prefetch_related(
            "activity", "flights", "lodgment", "transportation"
        )
    )

    # --- direct field filters ---
    if filtros.tipo:
        qs = qs.filter(tipo_producto=filtros.tipo)
    if filtros.precio_min is not None:
        qs = qs.filter(precio_unitario__gte=filtros.precio_min)
    if filtros.precio_max is not None:
        qs = qs.filter(precio_unitario__lte=filtros.precio_max)
    if filtros.supplier_id:
        qs = qs.filter(supplier_id=filtros.supplier_id)

    # --- related model filters ---
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

    # --- ordering ---
    if filtros.ordering:
        order_map = {
            "precio": "unit_price",
            "-precio": "-unit_price",
            "fecha": "activity__date",
            "-fecha": "-activity__date",
        }
        qs = qs.order_by(order_map.get(filtros.ordering, "unit_price"))

    # Paginate and serialize
    return [serialize_product_metadata(p) for p in qs]


@products_router.get("/{id}", response=ProductsMetadataOut)
def get_product(request, id: int):
    """
    Retrieve a single product metadata by its ID.

    Returns serialized metadata for the product if found.
    Raises HTTP 404 if no active record exists with the given ID.
    """
    metadata = get_object_or_404(
        ProductsMetadata.active.select_related("content_type"),
        id=id
    )
    return serialize_product_metadata(metadata)


TYPE_MAP = {
    ActivityUpdate:      "actividad",
    FlightUpdate:        "vuelo",
    LodgmentUpdate:      "alojamiento",
    TransportationUpdate:"transporte",
}

@products_router.patch("/update/{id}", response=ProductsMetadataOut)
@transaction.atomic
def update_product(request, id: int, data: ProductsMetadataUpdate):
    """
    Update product metadata and optionally its underlying product object.

    - Validates that the provided sub-schema matches the existing `product_type`.
    - Allows updating `unit_price` and `supplier_id`.
    - Applies partial updates to the real product (Activities, Flights, etc.) if included.
    - Raises HTTP 422 if attempting to change the product type or mismatched schema.
    """
    metadata = get_object_or_404(
        ProductsMetadata.objects.select_related("content_type"), id=id
    )

    if data.product is not None:
        expected = TYPE_MAP.get(type(data.product))
        if expected != metadata.product_type:
            raise HttpError(
                422,
                f"Provided sub-schema ({expected}) does not match product_type ({metadata.product_type})."
            )

    # Prevent product_type change
    if data.product and metadata.product_type != data.product.__class__.__name__.lower():
        raise HttpError(422, "Changing product_type is not allowed.")

    # Update metadata fields
    if data.unit_price is not None:
        if data.unit_price < 0:
            raise HttpError(400, "unit_price cannot be negative.")
        metadata.unit_price = data.unit_price

    if data.supplier_id is not None:
        metadata.supplier_id = data.supplier_id

    # Update underlying product fields
    if data.product is not None:
        producto = metadata.content
        for attr, value in data.product.dict(exclude_unset=True).items():
            setattr(producto, attr, value)
        producto.full_clean()
        producto.save(update_fields=list(data.product.dict(exclude_unset=True).keys()))

    metadata.save(update_fields=["unit_price", "supplier_id"])
    return serialize_product_metadata(metadata)


@products_router.patch("/deactivate/{id}", response={204: None})
@transaction.atomic
def deactivate_product(request, id: int):
    """
    Soft-deactivate a product metadata (and its underlying product) by ID.

    - Marks `is_active=False` and sets `deleted_at` timestamp.
    - Also deactivates the related domain object (Activities, Flights, etc.).
    - In the future, will check for confirmed sales before inactivation.
    """
    metadata = get_object_or_404(ProductsMetadata, id=id)

    metadata.is_active  = False
    metadata.deleted_at = timezone.now()
    metadata.save(update_fields=["is_active", "deleted_at"])

    # Also deactivate the real product instance
    metadata.content.is_active = False
    metadata.content.save(update_fields=["is_active"])

    return None