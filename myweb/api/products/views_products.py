from ninja import Router
from .schemas import (
    ProductsMetadataOut, ProductsMetadataCreate, ProductsMetadataUpdate,
    ActivityUpdate, FlightUpdate, LodgmentUpdate, TransportationUpdate,
    ActivityAvailabilityCreate, ActivityAvailabilityOut, ActivityAvailabilityUpdate,
    ActivityCompleteCreate, ActivityMetadataCreate, ActivityAvailabilityCreateNested,
    LodgmentCompleteCreate, LodgmentMetadataCreate, RoomCreateNested, RoomAvailabilityCreateNested,
    TransportationAvailabilityCreate, TransportationAvailabilityOut, TransportationAvailabilityUpdate,
    TransportationCompleteCreate, TransportationMetadataCreate, TransportationAvailabilityCreateNested,
    ProductsMetadataOutLodgmentDetail
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

@products_router.post("/products/create/", response=ProductsMetadataOut)
@transaction.atomic
def create_product(request, data: ProductsMetadataCreate):
    supplier = get_object_or_404(Suppliers, id=data.supplier_id)

    # Map product_type to model class
    model_map = {
        "actividad": Activities,
        "vuelo": Flights,
        "alojamiento": Lodgments,
        "transporte": Transportation,
    }
    Model = model_map.get(data.product_type)
    if not Model:
        raise HttpError(400, "Invalid product type")

    product = Model(**data.product.dict())

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


@products_router.post("/products/activity-complete/", response=ProductsMetadataOut)
@transaction.atomic
def create_complete_activity(request, data: ActivityCompleteCreate, metadata: ActivityMetadataCreate):
    """
    Crea una actividad completa con sus disponibilidades en una sola operación.
    """
    # 1. Verificar que el proveedor existe
    supplier = get_object_or_404(Suppliers, id=metadata.supplier_id)
    
    # 2. Crear la actividad
    activity_data = {
        "name": data.name,
        "description": data.description,
        "location_id": data.location_id,
        "date": data.date,
        "start_time": data.start_time,
        "duration_hours": data.duration_hours,
        "include_guide": data.include_guide,
        "maximum_spaces": data.maximum_spaces,
        "difficulty_level": data.difficulty_level,
        "language": data.language,
        "available_slots": data.available_slots,
    }
    
    activity = Activities(**activity_data)
    
    try:
        activity.full_clean()
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, error_detail)
    
    activity.save()
    
    # 3. Crear la metadata del producto
    content_type = ContentType.objects.get_for_model(Activities)
    
    metadata_obj = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=activity.id,
        unit_price=metadata.unit_price
    )
    
    # 4. Crear las disponibilidades si se proporcionan
    created_availabilities = []
    for availability_data in data.availabilities:
        availability = activity.availabilities.create(
            event_date=availability_data.event_date,
            start_time=availability_data.start_time,
            total_seats=availability_data.total_seats,
            reserved_seats=availability_data.reserved_seats,
            price=availability_data.price,
            currency=availability_data.currency,
            state="active"
        )
        created_availabilities.append(availability)
    
    return serialize_product_metadata(metadata_obj)


@products_router.post("/products/lodgment-complete/", response=ProductsMetadataOutLodgmentDetail)
@transaction.atomic
def create_complete_lodgment(request, data: LodgmentCompleteCreate, metadata: LodgmentMetadataCreate):
    """
    Crea un alojamiento completo con habitaciones y disponibilidades en una sola operación.
    """
    # 1. Verificar que el proveedor existe
    supplier = get_object_or_404(Suppliers, id=metadata.supplier_id)
    
    # 2. Crear el alojamiento
    lodgment_data = {
        "name": data.name,
        "description": data.description,
        "location_id": data.location_id,
        "type": data.type,
        "max_guests": data.max_guests,
        "contact_phone": data.contact_phone,
        "contact_email": data.contact_email,
        "amenities": data.amenities,
        "date_checkin": data.date_checkin,
        "date_checkout": data.date_checkout,
    }
    
    lodgment = Lodgment(**lodgment_data)
    
    try:
        lodgment.full_clean()
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, error_detail)
    
    lodgment.save()
    
    # 3. Crear la metadata del producto
    content_type = ContentType.objects.get_for_model(Lodgment)
    
    metadata_obj = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=lodgment.id,
        unit_price=metadata.unit_price
    )
    
    # 4. Crear las habitaciones y sus disponibilidades
    created_rooms = []
    for room_data in data.rooms:
        # Extraer las disponibilidades antes de crear la habitación
        room_availabilities = room_data.availabilities
        room_data_dict = room_data.dict(exclude={'availabilities'})
        
        # Crear la habitación
        room = lodgment.rooms.create(**room_data_dict)
        created_rooms.append(room)
        
        # Crear las disponibilidades de la habitación
        for availability_data in room_availabilities:
            room.availabilities.create(
                start_date=availability_data.start_date,
                end_date=availability_data.end_date,
                available_quantity=availability_data.available_quantity,
                price_override=availability_data.price_override,
                currency=availability_data.currency,
                is_blocked=availability_data.is_blocked,
                minimum_stay=availability_data.minimum_stay
            )
    
    return serialize_product_metadata(metadata_obj)


@products_router.post("/products/transport-complete/", response=ProductsMetadataOut)
@transaction.atomic
def create_complete_transport(request, data: TransportationCompleteCreate, metadata: TransportationMetadataCreate):
    """
    Crea un transporte completo con sus disponibilidades en una sola operación.
    """
    # 1. Verificar que el proveedor existe
    supplier = get_object_or_404(Suppliers, id=metadata.supplier_id)
    
    # 2. Crear el transporte
    transportation_data = {
        "origin_id": data.origin_id,
        "destination_id": data.destination_id,
        "type": data.type,
        "description": data.description,
        "notes": data.notes,
        "capacity": data.capacity,
    }
    
    transportation = Transportation(**transportation_data)
    
    try:
        transportation.full_clean()
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, error_detail)
    
    transportation.save()
    
    # 3. Crear la metadata del producto
    content_type = ContentType.objects.get_for_model(Transportation)
    
    metadata_obj = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=transportation.id,
        unit_price=metadata.unit_price
    )
    
    # 4. Crear las disponibilidades si se proporcionan
    created_availabilities = []
    for availability_data in data.availabilities:
        availability = transportation.availabilities.create(
            departure_date=availability_data.departure_date,
            departure_time=availability_data.departure_time,
            arrival_date=availability_data.arrival_date,
            arrival_time=availability_data.arrival_time,
            total_seats=availability_data.total_seats,
            reserved_seats=availability_data.reserved_seats,
            price=availability_data.price,
            currency=availability_data.currency,
            state=availability_data.state
        )
        created_availabilities.append(availability)
    
    return serialize_product_metadata(metadata_obj)


@products_router.post("/products/{id}/transportation-availability/", response=TransportationAvailabilityOut)
@transaction.atomic
def create_transportation_availability(request, id: int, data: TransportationAvailabilityCreate):
    metadata = get_object_or_404(ProductsMetadata.active.select_related("content_type_id"), id=id)

    if metadata.product_type != "transportation":
        raise HttpError(400, "This product is not a transportation.")

    transportation = metadata.content

    if not transportation.is_active:
        raise HttpError(400, "The transportation is inactive.")

    if data.reserved_seats > data.total_seats:
        raise HttpError(422, "Reserved seats cannot exceed total seats.")

    availability = transportation.availabilities.create(
        departure_date=data.departure_date,
        departure_time=data.departure_time,
        arrival_date=data.arrival_date,
        arrival_time=data.arrival_time,
        total_seats=data.total_seats,
        reserved_seats=data.reserved_seats,
        price=data.price,
        currency=data.currency,
        state=data.state,
    )

    return serialize_transportation_availability(availability)


@products_router.get("/products/{id}/transportation-availability/", response=List[TransportationAvailabilityOut])
def list_transportation_availabilities(request, id: int):
    # 1. Buscar el producto
    metadata = get_object_or_404(
        ProductsMetadata.active.select_related("content_type_id"), id=id
    )

    # 2. Validar tipo
    if metadata.product_type != "transportation":
        raise HttpError(400, "This product is not a transportation.")

    # 3. Obtener transporte concreto
    transportation = metadata.content

    # 4. Retornar todas las disponibilidades (ordenadas por fecha y hora)
    availabilities = transportation.availabilities.order_by("departure_date", "departure_time").all()
    return [serialize_transportation_availability(av) for av in availabilities]


@products_router.delete("/products/transportation-availability/{id}/", response={204: None})
@transaction.atomic
def delete_transportation_availability(request, id: int):
    # 1. Buscar la disponibilidad
    availability = get_object_or_404(TransportationAvailability, id=id)

    # 2. Eliminar directamente (hard-delete)
    availability.delete()

    # 3. Retornar vacío con status 204 (sin contenido)
    return 204, None


@products_router.patch("/products/transportation-availability/{id}/", response=TransportationAvailabilityOut)
@transaction.atomic
def update_transportation_availability(request, id: int, data: TransportationAvailabilityUpdate):
    availability = get_object_or_404(TransportationAvailability, id=id)

    # Validaciones cruzadas
    if data.reserved_seats is not None:
        total = data.total_seats if data.total_seats is not None else availability.total_seats
        if data.reserved_seats > total:
            raise HttpError(422, "Reserved seats cannot exceed total seats.")

    if data.departure_date is not None and data.departure_date < datetime.now().date():
        raise HttpError(422, "Departure date cannot be in the past.")

    # Aplicar cambios
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(availability, attr, value)

    availability.full_clean()
    availability.save()

    return serialize_transportation_availability(availability)


@products_router.post("/products/{id}/availability/", response=ActivityAvailabilityOut)
@transaction.atomic
def create_availability(request, id: int, data: ActivityAvailabilityCreate):
    metadata = get_object_or_404(ProductsMetadata.active.select_related("content_type_id"), id=id)

    if metadata.product_type != "activity":
        raise HttpError(400, "This product is not an activity.")

    activity = metadata.content

    if not activity.is_active:
        raise HttpError(400, "The activity is inactive.")

    if data.reserved_seats > data.total_seats:
        raise HttpError(422, "Reserved seats cannot exceed total seats.")

    availability = activity.availabilities.create(
        event_date=data.event_date,
        start_time=data.start_time,
        total_seats=data.total_seats,
        reserved_seats=data.reserved_seats,
        price=data.price,
        currency=data.currency,
        state=data.state,
    )

    return serialize_activity_availability(availability)

@products_router.get("/products/{id}/availability/", response=List[ActivityAvailabilityOut])
def list_availabilities(request, id: int):
    # 1. Buscar el producto
    metadata = get_object_or_404(
        ProductsMetadata.active.select_related("content_type_id"), id=id
    )

    # 2. Validar tipo
    if metadata.product_type != "activity":
        raise HttpError(400, "This product is not an activity.")

    # 3. Obtener actividad concreta
    activity = metadata.content

    # 4. Retornar todas las disponibilidades (ordenadas por fecha y hora)
    availabilities = activity.availabilities.order_by("event_date", "start_time").all()
    return [serialize_activity_availability(av) for av in availabilities]

@products_router.delete("/products/availability/{id}/", response={204: None})
@transaction.atomic
def delete_availability(request, id: int):
    # 1. Buscar la disponibilidad
    availability = get_object_or_404(ActivityAvailability, id=id)

    # 2. Eliminar directamente (hard-delete)
    availability.delete()

    # 3. Retornar vacío con status 204 (sin contenido)
    return 204, None

@products_router.patch("/products/availability/{id}/", response=ActivityAvailabilityOut)
@transaction.atomic
def update_availability(request, id: int, data: ActivityAvailabilityUpdate):
    availability = get_object_or_404(ActivityAvailability, id=id)

    # Validaciones cruzadas
    if data.reserved_seats is not None:
        total = data.total_seats if data.total_seats is not None else availability.total_seats
        if data.reserved_seats > total:
            raise HttpError(422, "Reserved seats cannot exceed total seats.")

    if data.event_date is not None and data.event_date < datetime.now().date():
        raise HttpError(422, "Event date cannot be in the past.")

    # Aplicar cambios
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(availability, attr, value)

    availability.full_clean()
    availability.save()

    return serialize_activity_availability(availability)


@products_router.get("/products/", response=list[ProductsMetadataOut])
@paginate(DefaultPagination)
def list_products(request, filters: ProductosFiltro = ProductosFiltro()):
    """
    Lista todos los productos con filtros avanzados y paginación
    """
    qs = ProductsMetadata.active.select_related(
        "supplier", "content_type_id"
    ).prefetch_related(
        "activity", "flight", "lodgment", "transportation"
    )

    # ──────────────────────────────────────────────────────────────
    # FILTROS BÁSICOS
    # ──────────────────────────────────────────────────────────────
    if filters.product_type:
        qs = qs.filter(product_type=filters.product_type)
    if filters.unit_price_min is not None:
        qs = qs.filter(unit_price__gte=filters.unit_price_min)
    if filters.unit_price_max is not None:
        qs = qs.filter(unit_price__lte=filters.unit_price_max)
    if filters.supplier_id:
        qs = qs.filter(supplier_id=filters.supplier_id)

    # ──────────────────────────────────────────────────────────────
    # FILTROS DE PRECIO
    # ──────────────────────────────────────────────────────────────
    if filters.unit_price_min is not None:
        qs = qs.filter(unit_price__gte=filters.unit_price_min)
    if filters.unit_price_max is not None:
        qs = qs.filter(unit_price__lte=filters.unit_price_max)
    
    # Filtros de precio por noche para alojamientos
    if filters.price_per_night_min is not None:
        qs = qs.filter(lodgment__rooms__base_price_per_night__gte=filters.price_per_night_min)
    if filters.price_per_night_max is not None:
        qs = qs.filter(lodgment__rooms__base_price_per_night__lte=filters.price_per_night_max)
    
    if filters.supplier_id:
        qs = qs.filter(supplier_id=filters.supplier_id)

    # ──────────────────────────────────────────────────────────────
    # FILTRO DE BÚSQUEDA POR TEXTO
    # ──────────────────────────────────────────────────────────────
    if filters.search:
        qs = qs.filter(
            Q(activity__name__icontains=filters.search) |
            Q(activity__description__icontains=filters.search) |
            Q(flights__airline__icontains=filters.search) |
            Q(flights__flight_number__icontains=filters.search) |
            Q(lodgment__name__icontains=filters.search) |
            Q(lodgment__description__icontains=filters.search) |
            Q(transportation__description__icontains=filters.search) |
            Q(supplier__organization_name__icontains=filters.search)
        )

    # ──────────────────────────────────────────────────────────────
    # FILTROS DE UBICACIÓN
    # ──────────────────────────────────────────────────────────────
    if filters.destination_id:
        qs = qs.filter(
            Q(flights__destination_id=filters.destination_id) |
            Q(transportation__destination_id=filters.destination_id) |
            Q(lodgment__location_id=filters.destination_id) |
            Q(activity__location_id=filters.destination_id)
        )
    if filters.origin_id:
        qs = qs.filter(
            Q(flights__origin_id=filters.origin_id) |
            Q(transportation__origin_id=filters.origin_id)
        )
    if filters.location_id:
        qs = qs.filter(
            Q(lodgment__location_id=filters.location_id) |
            Q(activity__location_id=filters.location_id)
        )

    # ──────────────────────────────────────────────────────────────
    # FILTROS DE FECHAS
    # ──────────────────────────────────────────────────────────────
    if filters.date_min:
        qs = qs.filter(
            Q(activity__date__gte=filters.date_min) |
            Q(flights__departure_date__gte=filters.date_min) |
            Q(transportation__departure_date__gte=filters.date_min) |
            Q(lodgment__date_checkin__gte=filters.date_min)
        )
    if filters.date_max:
        qs = qs.filter(
            Q(activity__date__lte=filters.date_max) |
            Q(flights__departure_date__lte=filters.date_max) |
            Q(transportation__departure_date__lte=filters.date_max) |
            Q(lodgment__date_checkin__lte=filters.date_max)
        )
    if filters.date_checkin:
        qs = qs.filter(lodgment__date_checkin__gte=filters.date_checkin)
    if filters.date_checkout:
        qs = qs.filter(lodgment__date_checkout__lte=filters.date_checkout)
    if filters.date_departure:
        qs = qs.filter(
            Q(flights__departure_date__gte=filters.date_departure) |
            Q(transportation__departure_date__gte=filters.date_departure)
        )
    if filters.date_arrival:
        qs = qs.filter(
            Q(flights__arrival_date__lte=filters.date_arrival) |
            Q(transportation__arrival_date__lte=filters.date_arrival)
        )

    # ──────────────────────────────────────────────────────────────
    # FILTROS DE DISPONIBILIDAD
    # ──────────────────────────────────────────────────────────────
    if filters.available_only:
        qs = qs.filter(is_active=True)
    if filters.capacity_min is not None:
        qs = qs.filter(
            Q(activity__maximum_spaces__gte=filters.capacity_min) |
            Q(flights__available_seats__gte=filters.capacity_min) |
            Q(transportation__capacity__gte=filters.capacity_min)
        )
    if filters.capacity_max is not None:
        qs = qs.filter(
            Q(activity__maximum_spaces__lte=filters.capacity_max) |
            Q(flights__available_seats__lte=filters.capacity_max) |
            Q(transportation__capacity__lte=filters.capacity_max)
        )
    
    # Filtros de asientos disponibles
    if filters.available_seats_min is not None:
        qs = qs.filter(
            Q(activity__availabilities__total_seats__gte=filters.available_seats_min) |
            Q(flights__available_seats__gte=filters.available_seats_min) |
            Q(transportation__availabilities__total_seats__gte=filters.available_seats_min)
        )
    if filters.available_seats_max is not None:
        qs = qs.filter(
            Q(activity__availabilities__total_seats__lte=filters.available_seats_max) |
            Q(flights__available_seats__lte=filters.available_seats_max) |
            Q(transportation__availabilities__total_seats__lte=filters.available_seats_max)
        )

    # ──────────────────────────────────────────────────────────────
    # FILTROS ESPECÍFICOS PARA ACTIVIDADES
    # ──────────────────────────────────────────────────────────────
    if filters.difficulty_level:
        qs = qs.filter(activity__difficulty_level=filters.difficulty_level)
    if filters.include_guide is not None:
        qs = qs.filter(activity__include_guide=filters.include_guide)
    if filters.language:
        qs = qs.filter(activity__language__icontains=filters.language)
    if filters.duration_min is not None:
        qs = qs.filter(activity__duration_hours__gte=filters.duration_min)
    if filters.duration_max is not None:
        qs = qs.filter(activity__duration_hours__lte=filters.duration_max)

    # ──────────────────────────────────────────────────────────────
    # FILTROS ESPECÍFICOS PARA VUELOS
    # ──────────────────────────────────────────────────────────────
    if filters.airline:
        qs = qs.filter(flights__airline__icontains=filters.airline)
    if filters.class_flight:
        qs = qs.filter(flights__class_flight=filters.class_flight)
    if filters.duration_flight_min is not None:
        qs = qs.filter(flights__duration_hours__gte=filters.duration_flight_min)
    if filters.duration_flight_max is not None:
        qs = qs.filter(flights__duration_hours__lte=filters.duration_flight_max)
    if filters.direct_flight is not None:
        # Para vuelos directos, verificamos que origen y destino sean diferentes
        if filters.direct_flight:
            qs = qs.filter(
                ~Q(flights__origin_id=F('flights__destination_id'))
            )

    # ──────────────────────────────────────────────────────────────
    # FILTROS ESPECÍFICOS PARA ALOJAMIENTOS
    # ──────────────────────────────────────────────────────────────
    if filters.lodgment_type:
        qs = qs.filter(lodgment__type=filters.lodgment_type)
    if filters.room_type:
        qs = qs.filter(lodgment__rooms__room_type=filters.room_type)
    if filters.guests_min is not None:
        qs = qs.filter(lodgment__max_guests__gte=filters.guests_min)
    if filters.guests_max is not None:
        qs = qs.filter(lodgment__max_guests__lte=filters.guests_max)
    if filters.nights_min is not None:
        # Calcular la diferencia entre checkin y checkout
        from django.db.models import F
        qs = qs.filter(
            lodgment__date_checkout__gte=F('lodgment__date_checkin') + timedelta(days=filters.nights_min)
        )
    if filters.nights_max is not None:
        # Calcular la diferencia entre checkin y checkout
        from django.db.models import F
        qs = qs.filter(
            lodgment__date_checkout__lte=F('lodgment__date_checkin') + timedelta(days=filters.nights_max)
        )
    if filters.amenities:
        for amenidad in filters.amenities:
            qs = qs.filter(lodgment__amenities__contains=amenidad)

    # ──────────────────────────────────────────────────────────────
    # FILTROS DE CARACTERÍSTICAS DE HABITACIÓN
    # ──────────────────────────────────────────────────────────────
    if filters.private_bathroom is not None:
        qs = qs.filter(lodgment__rooms__has_private_bathroom=filters.private_bathroom)
    if filters.balcony is not None:
        qs = qs.filter(lodgment__rooms__has_balcony=filters.balcony)
    if filters.air_conditioning is not None:
        qs = qs.filter(lodgment__rooms__has_air_conditioning=filters.air_conditioning)
    if filters.wifi is not None:
        qs = qs.filter(lodgment__rooms__has_wifi=filters.wifi)

    # ──────────────────────────────────────────────────────────────
    # FILTROS ESPECÍFICOS PARA TRANSPORTE
    # ──────────────────────────────────────────────────────────────
    if filters.transport_type:
        qs = qs.filter(transportation__type=filters.transport_type)

    # ──────────────────────────────────────────────────────────────
    # ORDENAMIENTO
    # ──────────────────────────────────────────────────────────────
    if filters.ordering:
        order_map = {
            "unit_price": "unit_price",
            "-unit_price": "-unit_price",
            "date": "activity__date",
            "-date": "-activity__date",
            "name": "activity__name",
            "-name": "-activity__name",
            "rating": "unit_price",  # Placeholder - implementar rating cuando esté disponible
            "-rating": "-unit_price",
            "popularity": "unit_price",  # Placeholder - implementar popularidad cuando esté disponible
            "-popularity": "-unit_price",
        }
        qs = qs.order_by(order_map.get(filters.ordering, "unit_price"))

    # ──────────────────────────────────────────────────────────────
    # FILTROS AVANZADOS (PLACEHOLDERS)
    # ──────────────────────────────────────────────────────────────
    if filters.rating_min is not None:
        # Placeholder - implementar cuando el modelo de ratings esté disponible
        # qs = qs.filter(average_rating__gte=filters.rating_min)
        pass
    if filters.rating_max is not None:
        # Placeholder - implementar cuando el modelo de ratings esté disponible
        # qs = qs.filter(average_rating__lte=filters.rating_max)
        pass
    if filters.promotions_only:
        # Placeholder - implementar cuando el modelo de promociones esté disponible
        # qs = qs.filter(promotions__is_active=True)
        pass
    if filters.last_minute:
        # Placeholder - implementar lógica de ofertas de última hora
        # qs = qs.filter(is_last_minute=True)
        pass
    if filters.featured_only:
        # Placeholder - implementar lógica de productos destacados
        # qs = qs.filter(is_featured=True)
        pass

    # ──────────────────────────────────────────────────────────────
    # DISTINCT PARA EVITAR DUPLICADOS
    # ──────────────────────────────────────────────────────────────
    qs = qs.distinct()

    return qs


@products_router.get("/products/{id}/", response=ProductsMetadataOut)
def get_product(request, id: int):
    metadata = get_object_or_404(ProductsMetadata.active.select_related("content_type_id"), id=id)
    return serialize_product_metadata(metadata)


@products_router.patch("/products/{id}/", response=ProductsMetadataOut)
@transaction.atomic
def update_product(request, id: int, data: ProductsMetadataUpdate):
    metadata = get_object_or_404(ProductsMetadata.active.select_related("content_type_id"), id=id)

    # Actualizar campos de metadata si se proporcionan
    if data.unit_price is not None:
        if data.unit_price < 0:
            raise HttpError(400, "The price cannot be negative")
        metadata.unit_price = data.unit_price

    if data.supplier_id is not None:
        metadata.supplier_id = data.supplier_id

    # Actualizar el producto si se proporciona
    if data.product is not None:
        product = metadata.content
        product_fields = data.product.dict(exclude_unset=True)

        # Validar campos válidos para el tipo de producto
        valid_fields = {
            "activity": [
                "name", "description", "location_id", "date", "start_time", 
                "duration_hours", "include_guide", "maximum_spaces", 
                "difficulty_level", "language", "available_slots"
            ],
            "flight": [
                "airline", "flight_number", "origin_id", "destination_id",
                "departure_date", "departure_time", "arrival_date", "arrival_time",
                "duration_hours", "class_flight", "available_seats", "luggage_info",
                "aircraft_type", "terminal", "gate", "notes"
            ],
            "lodgment": [
                "name", "description", "location_id", "type", "max_guests",
                "contact_phone", "contact_email", "amenities", "date_checkin",
                "date_checkout", "is_active"
            ],
            "transportation": [
                "origin_id", "destination_id", "type", "description", "notes",
                "capacity", "is_active"
            ]
        }
        print(f"[DEBUG] Tipo de producto: {metadata.product_type}")
        print(f"[DEBUG] Campos recibidos: {list(product_fields.keys())}")
        print(f"[DEBUG] Campos válidos: {valid_fields.get(metadata.product_type, [])}")
        valid_fields_for_type = valid_fields.get(metadata.product_type, [])
        invalid_fields = [field for field in product_fields.keys() if field not in valid_fields_for_type]
        if invalid_fields:
            print(f"[DEBUG] Campos inválidos detectados: {invalid_fields} para tipo {metadata.product_type}")
            raise HttpError(
                422,
                f"The fields {invalid_fields} are not valid for products of type {metadata.product_type}"
            )
        # Aplicar los cambios al producto SOLO si el atributo existe
        for attr, value in product_fields.items():
            if not hasattr(product, attr):
                raise HttpError(422, f"Field '{attr}' does not exist on product type '{metadata.product_type}'")
            setattr(product, attr, value)
        try:
            # Refrescar el objeto desde la base antes de validar
            product.refresh_from_db()
            product.full_clean()
            product.save()
        except ValidationError as e:
            error_messages = []
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
            else:
                error_messages.append(str(e))
            error_detail = "; ".join(error_messages)
            raise HttpError(422, error_detail)
        except Exception as e:
            raise HttpError(422, str(e))

    metadata.save(update_fields=["unit_price", "supplier_id"])
    return serialize_product_metadata(metadata)


@products_router.delete("/products/{id}/", response={204: None})
@transaction.atomic
def deactivate_product(request, id: int):
    metadata = get_object_or_404(ProductsMetadata.active, id=id)
    metadata.is_active = False
    metadata.deleted_at = timezone.now()
    metadata.save()
    
    # También desactivar el producto relacionado
    product = metadata.content
    if hasattr(product, 'is_active'):
        product.is_active = False
        product.save(update_fields=['is_active'])
    
    return 204, None


@products_router.get("/products/search/advanced/", response=list[ProductsMetadataOut])
@paginate(DefaultPagination)
def advanced_search(request, filters: ProductosFiltro = ProductosFiltro()):
    """
    Búsqueda avanzada con filtros combinados y lógica más sofisticada
    """
    qs = ProductsMetadata.active.select_related(
        "supplier", "content_type_id"
    ).prefetch_related(
        "activity", "flight", "lodgment", "transportation",
        "activity__availabilities", "transportation__availabilities"
    )

    # Aplicar todos los filtros de la función principal
    qs = list_products(request, filters)
    
    # Lógica adicional para búsqueda avanzada
    if filters.search:
        # Búsqueda más sofisticada con ponderación
        search_terms = filters.search.split()
        search_queries = Q()
        
        for term in search_terms:
            term_query = (
                Q(activity__name__icontains=term) |
                Q(activity__description__icontains=term) |
                Q(flights__airline__icontains=term) |
                Q(flights__flight_number__icontains=term) |
                Q(lodgment__name__icontains=term) |
                Q(lodgment__description__icontains=term) |
                Q(transportation__description__icontains=term) |
                Q(supplier__organization_name__icontains=term)
            )
            search_queries &= term_query
        
        qs = qs.filter(search_queries)
    
    # Filtros de disponibilidad en tiempo real
    if filters.available_only:
        today = timezone.now().date()
        qs = qs.filter(
            Q(activity__availabilities__event_date__gte=today) |
            Q(flights__available_seats__gt=0) |
            Q(transportation__availabilities__total_seats__gt=F('transportation__availabilities__reserved_seats')) |
            Q(lodgment__rooms__availabilities__available_quantity__gt=0)
        )
    
    # Ordenamiento por relevancia si no se especifica otro
    if not filters.ordering:
        qs = qs.order_by('-unit_price')  # Por defecto, ordenar por precio descendente
    
    return qs


@products_router.get("/products/search/quick/", response=list[ProductsMetadataOut])
def quick_search(request, q: str, limit: int = 10):
    """
    Búsqueda rápida por texto con límite de resultados
    """
    qs = ProductsMetadata.active.select_related(
        "supplier", "content_type_id"
    ).prefetch_related(
        "activity", "flight", "lodgment", "transportation"
    )
    
    # Búsqueda simple por texto
    qs = qs.filter(
        Q(activity__name__icontains=q) |
        Q(activity__description__icontains=q) |
        Q(flights__airline__icontains=q) |
        Q(flights__flight_number__icontains=q) |
        Q(lodgment__name__icontains=q) |
        Q(lodgment__description__icontains=q) |
        Q(transportation__description__icontains=q) |
        Q(supplier__organization_name__icontains=q)
    ).distinct()[:limit]
    
    return qs


@products_router.get("/products/stats/filters/")
def get_filter_stats(request):
    """
    Obtiene estadísticas para ayudar con los filtros
    """
    from django.db.models import Count, Min, Max, Avg
    
    stats = {
        "price_range": {
            "min": ProductsMetadata.active.aggregate(Min('unit_price'))['unit_price__min'] or 0,
            "max": ProductsMetadata.active.aggregate(Max('unit_price'))['unit_price__max'] or 0,
            "avg": ProductsMetadata.active.aggregate(Avg('unit_price'))['unit_price__avg'] or 0,
        },
        "product_types": {
            "activity": ProductsMetadata.active.filter(product_type="activity").count(),
            "flight": ProductsMetadata.active.filter(product_type="flight").count(),
            "lodgment": ProductsMetadata.active.filter(product_type="lodgment").count(),
            "transportation": ProductsMetadata.active.filter(product_type="transportation").count(),
        },
        "locations": {
            "total": Location.objects.count(),
        },
        "suppliers": {
            "total": Suppliers.active.count(),
        }
    }
    
    return stats
