from ninja import Router
from .schemas import (
    ProductsMetadataOut, ProductsMetadataCreate, ProductsMetadataUpdate,
    ActivityUpdate, FlightUpdate, LodgmentUpdate, TransportationUpdate,
    ActivityAvailabilityCreate, ActivityAvailabilityOut, ActivityAvailabilityUpdate,
    ActivityFullCreate, ActivityAvailabilityCreateNested,
    LodgmentFullCreate, RoomCreateNested, RoomAvailabilityCreateNested,
    TransportationAvailabilityCreate, TransportationAvailabilityOut, TransportationAvailabilityUpdate,
    TransportationFullCreate, TransportationAvailabilityCreateNested
)
from .helpers import serialize_product_metadata, serialize_activity_availability, serialize_transportation_availability
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from .models import (
    ProductsMetadata, Suppliers,
    Activities, Flights, Lodgments, Transportation, ActivityAvailability, TransportationAvailability
)
from django.db.models import Q
from ninja.pagination import paginate
from .filters import ProductosFiltro
from .pagination import DefaultPagination
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from typing import List
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType

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
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, error_detail)

    # 3️⃣ Save valid domain object
    product.save()

    # Obtener el ContentType para el modelo
    content_type = ContentType.objects.get_for_model(_model)

    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=product.id,
        unit_price=data.unit_price
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
        .select_related("content_type_id")
        .prefetch_related(
            "activity",
            "flights",
            "lodgment",
            "transportation",
        )
    )

    # ──────────────────────────────────────────────────────────────
    # FILTROS BÁSICOS
    # ──────────────────────────────────────────────────────────────
    if filtros.tipo:
        qs = qs.filter(tipo_producto=filtros.tipo)
    if filtros.precio_min is not None:
        qs = qs.filter(precio_unitario__gte=filtros.precio_min)
    if filtros.precio_max is not None:
        qs = qs.filter(precio_unitario__lte=filtros.precio_max)
    if filtros.supplier_id:
        qs = qs.filter(supplier_id=filtros.supplier_id)

    # ──────────────────────────────────────────────────────────────
    # FILTROS DE UBICACIÓN
    # ──────────────────────────────────────────────────────────────
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
    if filtros.location_id:
        qs = qs.filter(
            Q(lodgment__location_id=filtros.location_id) |
            Q(activity__location_id=filtros.location_id)
        )

    # ──────────────────────────────────────────────────────────────
    # FILTROS DE FECHAS
    # ──────────────────────────────────────────────────────────────
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
    if filtros.fecha_checkin:
        qs = qs.filter(lodgment__date_checkin__gte=filtros.fecha_checkin)
    if filtros.fecha_checkout:
        qs = qs.filter(lodgment__date_checkout__lte=filtros.fecha_checkout)
    if filtros.fecha_salida:
        qs = qs.filter(
            Q(flights__departure_date__gte=filtros.fecha_salida) |
            Q(transportation__departure_date__gte=filtros.fecha_salida)
        )
    if filtros.fecha_llegada:
        qs = qs.filter(
            Q(flights__arrival_date__lte=filtros.fecha_llegada) |
            Q(transportation__arrival_date__lte=filtros.fecha_llegada)
        )

    # ──────────────────────────────────────────────────────────────
    # FILTROS DE DISPONIBILIDAD
    # ──────────────────────────────────────────────────────────────
    if filtros.disponibles_solo:
        qs = qs.filter(is_active=True)
    if filtros.capacidad_min is not None:
        qs = qs.filter(
            Q(activity__maximum_spaces__gte=filtros.capacidad_min) |
            Q(flights__available_seats__gte=filtros.capacidad_min) |
            Q(transportation__capacity__gte=filtros.capacidad_min)
        )
    if filtros.capacidad_max is not None:
        qs = qs.filter(
            Q(activity__maximum_spaces__lte=filtros.capacidad_max) |
            Q(flights__available_seats__lte=filtros.capacidad_max) |
            Q(transportation__capacity__lte=filtros.capacidad_max)
        )

    # ──────────────────────────────────────────────────────────────
    # FILTROS ESPECÍFICOS PARA ACTIVIDADES
    # ──────────────────────────────────────────────────────────────
    if filtros.nivel_dificultad:
        qs = qs.filter(activity__difficulty_level=filtros.nivel_dificultad)
    if filtros.incluye_guia is not None:
        qs = qs.filter(activity__include_guide=filtros.incluye_guia)
    if filtros.idioma:
        qs = qs.filter(activity__language__icontains=filtros.idioma)
    if filtros.duracion_min is not None:
        qs = qs.filter(activity__duration_hours__gte=filtros.duracion_min)
    if filtros.duracion_max is not None:
        qs = qs.filter(activity__duration_hours__lte=filtros.duracion_max)

    # ──────────────────────────────────────────────────────────────
    # FILTROS ESPECÍFICOS PARA VUELOS
    # ──────────────────────────────────────────────────────────────
    if filtros.aerolinea:
        qs = qs.filter(flights__airline__icontains=filtros.aerolinea)
    if filtros.clase_vuelo:
        qs = qs.filter(flights__class_flight=filtros.clase_vuelo)
    if filtros.duracion_vuelo_min is not None:
        qs = qs.filter(flights__duration_hours__gte=filtros.duracion_vuelo_min)
    if filtros.duracion_vuelo_max is not None:
        qs = qs.filter(flights__duration_hours__lte=filtros.duracion_vuelo_max)

    # ──────────────────────────────────────────────────────────────
    # FILTROS ESPECÍFICOS PARA ALOJAMIENTOS
    # ──────────────────────────────────────────────────────────────
    if filtros.tipo_alojamiento:
        qs = qs.filter(lodgment__type=filtros.tipo_alojamiento)
    if filtros.tipo_habitacion:
        qs = qs.filter(lodgment__rooms__room_type=filtros.tipo_habitacion)
    if filtros.huespedes_min is not None:
        qs = qs.filter(lodgment__max_guests__gte=filtros.huespedes_min)
    if filtros.huespedes_max is not None:
        qs = qs.filter(lodgment__max_guests__lte=filtros.huespedes_max)
    if filtros.noches_min is not None:
        # Calcular la diferencia entre checkin y checkout
        from django.db.models import F
        qs = qs.filter(
            lodgment__date_checkout__gte=F('lodgment__date_checkin') + timedelta(days=filtros.noches_min)
        )
    if filtros.amenidades:
        for amenidad in filtros.amenidades:
            qs = qs.filter(lodgment__amenities__contains=amenidad)

    # ──────────────────────────────────────────────────────────────
    # FILTROS DE CARACTERÍSTICAS DE HABITACIÓN
    # ──────────────────────────────────────────────────────────────
    if filtros.bano_privado is not None:
        qs = qs.filter(lodgment__rooms__has_private_bathroom=filtros.bano_privado)
    if filtros.balcon is not None:
        qs = qs.filter(lodgment__rooms__has_balcony=filtros.balcon)
    if filtros.aire_acondicionado is not None:
        qs = qs.filter(lodgment__rooms__has_air_conditioning=filtros.aire_acondicionado)
    if filtros.wifi is not None:
        qs = qs.filter(lodgment__rooms__has_wifi=filtros.wifi)

    # ──────────────────────────────────────────────────────────────
    # FILTROS DE BÚSQUEDA
    # ──────────────────────────────────────────────────────────────
    if filtros.search:
        qs = qs.filter(
            Q(activity__name__icontains=filtros.search) |
            Q(activity__description__icontains=filtros.search) |
            Q(flights__airline__icontains=filtros.search) |
            Q(flights__flight_number__icontains=filtros.search) |
            Q(lodgment__name__icontains=filtros.search) |
            Q(lodgment__description__icontains=filtros.search) |
            Q(transportation__description__icontains=filtros.search)
        )

    # ──────────────────────────────────────────────────────────────
    # FILTROS DE ORDENAMIENTO
    # ──────────────────────────────────────────────────────────────
    if filtros.ordering:
        order_map = {
            "precio": "unit_price",
            "-precio": "-unit_price",
            "fecha": "activity__date",
            "-fecha": "-activity__date",
            "nombre": "activity__name",
            "-nombre": "-activity__name",
            "rating": "unit_price",  # Placeholder - implementar rating cuando esté disponible
            "-rating": "-unit_price",
            "popularidad": "unit_price",  # Placeholder - implementar popularidad cuando esté disponible
            "-popularidad": "-unit_price",
        }
        qs = qs.order_by(order_map.get(filtros.ordering, "unit_price"))

    # ──────────────────────────────────────────────────────────────
    # FILTROS AVANZADOS
    # ──────────────────────────────────────────────────────────────
    if filtros.rating_min is not None:
        # Placeholder - implementar cuando el modelo de reviews esté disponible
        # qs = qs.filter(average_rating__gte=filtros.rating_min)
        pass
    if filtros.rating_max is not None:
        # Placeholder - implementar cuando el modelo de reviews esté disponible
        # qs = qs.filter(average_rating__lte=filtros.rating_max)
        pass
    if filtros.promociones_solo:
        # Placeholder - implementar cuando el modelo de promociones esté disponible
        # qs = qs.filter(promotions__is_active=True)
        pass
    if filtros.ultima_hora:
        # Placeholder - implementar lógica de ofertas de última hora
        # qs = qs.filter(is_last_minute=True)
        pass

    return [serialize_product_metadata(p) for p in qs]


@products_router.get("/{id}", response=ProductsMetadataOut)
def get_product(request, id: int):
    """
    Retrieve a single product metadata by its ID.

    Returns serialized metadata for the product if found.
    Raises HTTP 404 if no active record exists with the given ID.
    """
    metadata = get_object_or_404(
        ProductsMetadata.active.select_related("content_type_id"),
        id=id
    )
    return serialize_product_metadata(metadata)


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

    # Actualizar campos de metadata si se proporcionan
    if data.precio_unitario is not None:
        if data.precio_unitario < 0:
            raise HttpError(400, "El precio no puede ser negativo")
        metadata.precio_unitario = data.precio_unitario

    if data.supplier_id is not None:
        metadata.supplier_id = data.supplier_id

    # Actualizar el producto si se proporciona
    if data.producto is not None:
        producto = metadata.content

        # Validar que los campos del producto son válidos para el tipo de producto
        producto_fields = data.producto.dict(exclude_unset=True)

        # Verificar que no se estén actualizando campos que no corresponden al tipo de producto
        valid_fields = {
            "activity": ["name", "description", "location_id", "date", "start_time",
                        "duration_hours", "include_guide", "maximum_spaces",
                        "difficulty_level", "language", "available_slots"],
            "flight": ["airline", "flight_number", "origin_id", "destination_id",
                      "departure_date", "departure_time", "arrival_date", "arrival_time",
                      "duration_hours", "class_flight", "available_seats", "luggage_info",
                      "aircraft_type", "terminal", "gate", "notes"],
            "lodgment": ["name", "description", "location_id", "type", "max_guests",
                        "contact_phone", "contact_email", "amenities", "date_checkin",
                        "date_checkout"],
            "transportation": ["origin_id", "destination_id", "type", "description",
                             "notes", "capacity"]
        }

        valid_fields_for_type = valid_fields.get(metadata.tipo_producto, [])
        invalid_fields = [field for field in producto_fields.keys() if field not in valid_fields_for_type]

        if invalid_fields:
            raise HttpError(
                422,
                f"Los campos {invalid_fields} no son válidos para productos de tipo {metadata.tipo_producto}"
            )

        # Aplicar los cambios al producto
        for attr, value in producto_fields.items():
            setattr(producto, attr, value)

        try:
            producto.full_clean()
        except ValidationError as e:
            error_messages = []
            for field, errors in e.message_dict.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            error_detail = "; ".join(error_messages)
            raise HttpError(422, error_detail)

        producto.save(update_fields=list(producto_fields.keys()))

    metadata.save(update_fields=["precio_unitario", "supplier_id"])

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

    # ───── TODO: reactivar esta lógica cuando el modelo Order exista ─────
    # tiene_ventas_confirmadas = metadata.orders.filter(status="confirmed").exists()
    # if tiene_ventas_confirmadas:
    #     # Solo inactivamos metadata; no tocamos el objeto real para preservar trazabilidad
    #     metadata.is_active = False
    #     metadata.deleted_at = timezone.now()
    #     metadata.save(update_fields=["is_active", "deleted_at"])
    #     return 204, None
    # ─────────────────────────────────────────────────────────────────────

    # Versión temporal: siempre inactivamos tanto metadata como el objeto real
    metadata.is_active = False
    metadata.deleted_at = timezone.now()
    metadata.save(update_fields=["is_active", "deleted_at"])

    # Also deactivate the real product instance
    metadata.content.is_active = False
    metadata.content.save(update_fields=["is_active"])

    return None