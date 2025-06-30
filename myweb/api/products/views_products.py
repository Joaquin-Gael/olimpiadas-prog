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
    Activities, Flights, Lodgment, Transportation, ActivityAvailability, TransportationAvailability
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

products_router = Router(tags=["Productos"])

@products_router.post("/productos/crear/", response=ProductsMetadataOut)
@transaction.atomic
def crear_producto(request, data: ProductsMetadataCreate):
    supplier = get_object_or_404(Suppliers, id=data.supplier_id)

    model_map = {
        "activity": Activities,
        "flight": Flights,
        "lodgment": Lodgment,
        "transportation": Transportation,
    }
    Model = model_map.get(data.tipo_producto)
    if not Model:
        raise HttpError(400, "Tipo de producto no válido")

    producto = Model(**data.producto.dict())

    try:
        producto.full_clean()
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, error_detail)

    producto.save()

    # Obtener el ContentType para el modelo
    content_type = ContentType.objects.get_for_model(Model)
    
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=producto.id,
        precio_unitario=data.precio_unitario
    )

    return serialize_product_metadata(metadata)


@products_router.post("/productos/actividad-completa/", response=ProductsMetadataOut)
@transaction.atomic
def crear_actividad_completa(request, data: ActivityFullCreate):
    """
    Crea una actividad completa con sus disponibilidades en una sola operación.
    """
    # 1. Verificar que el proveedor existe
    supplier = get_object_or_404(Suppliers, id=data.supplier_id)
    
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
    
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=activity.id,
        precio_unitario=data.precio_unitario
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
    
    return serialize_product_metadata(metadata)


@products_router.post("/productos/alojamiento-completo/", response=ProductsMetadataOut)
@transaction.atomic
def crear_alojamiento_completo(request, data: LodgmentFullCreate):
    """
    Crea un alojamiento completo con habitaciones y disponibilidades en una sola operación.
    """
    # 1. Verificar que el proveedor existe
    supplier = get_object_or_404(Suppliers, id=data.supplier_id)
    
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
    
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=lodgment.id,
        precio_unitario=data.precio_unitario
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
    
    return serialize_product_metadata(metadata)


@products_router.post("/productos/transporte-completo/", response=ProductsMetadataOut)
@transaction.atomic
def crear_transporte_completo(request, data: TransportationFullCreate):
    """
    Crea un transporte completo con sus disponibilidades en una sola operación.
    """
    # 1. Verificar que el proveedor existe
    supplier = get_object_or_404(Suppliers, id=data.supplier_id)
    
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
    
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=transportation.id,
        precio_unitario=data.precio_unitario
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
    
    return serialize_product_metadata(metadata)


@products_router.post("/productos/{id}/transportation-availability/", response=TransportationAvailabilityOut)
@transaction.atomic
def create_transportation_availability(request, id: int, data: TransportationAvailabilityCreate):
    metadata = get_object_or_404(ProductsMetadata.active.select_related("content_type_id"), id=id)

    if metadata.tipo_producto != "transportation":
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


@products_router.get("/productos/{id}/transportation-availability/", response=List[TransportationAvailabilityOut])
def list_transportation_availabilities(request, id: int):
    # 1. Buscar el producto
    metadata = get_object_or_404(
        ProductsMetadata.active.select_related("content_type_id"), id=id
    )

    # 2. Validar tipo
    if metadata.tipo_producto != "transportation":
        raise HttpError(400, "This product is not a transportation.")

    # 3. Obtener transporte concreto
    transportation = metadata.content

    # 4. Retornar todas las disponibilidades (ordenadas por fecha y hora)
    availabilities = transportation.availabilities.order_by("departure_date", "departure_time").all()
    return [serialize_transportation_availability(av) for av in availabilities]


@products_router.delete("/productos/transportation-availability/{id}/", response={204: None})
@transaction.atomic
def delete_transportation_availability(request, id: int):
    # 1. Buscar la disponibilidad
    availability = get_object_or_404(TransportationAvailability, id=id)

    # 2. Eliminar directamente (hard-delete)
    availability.delete()

    # 3. Retornar vacío con status 204 (sin contenido)
    return 204, None


@products_router.patch("/productos/transportation-availability/{id}/", response=TransportationAvailabilityOut)
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


@products_router.post("/productos/{id}/availability/", response=ActivityAvailabilityOut)
@transaction.atomic
def create_availability(request, id: int, data: ActivityAvailabilityCreate):
    metadata = get_object_or_404(ProductsMetadata.active.select_related("content_type_id"), id=id)

    if metadata.tipo_producto != "activity":
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

@products_router.get("/productos/{id}/availability/", response=List[ActivityAvailabilityOut])
def list_availabilities(request, id: int):
    # 1. Buscar el producto
    metadata = get_object_or_404(
        ProductsMetadata.active.select_related("content_type_id"), id=id
    )

    # 2. Validar tipo
    if metadata.tipo_producto != "activity":
        raise HttpError(400, "This product is not an activity.")

    # 3. Obtener actividad concreta
    activity = metadata.content

    # 4. Retornar todas las disponibilidades (ordenadas por fecha y hora)
    availabilities = activity.availabilities.order_by("event_date", "start_time").all()
    return [serialize_activity_availability(av) for av in availabilities]

@products_router.delete("/productos/availability/{id}/", response={204: None})
@transaction.atomic
def delete_availability(request, id: int):
    # 1. Buscar la disponibilidad
    availability = get_object_or_404(ActivityAvailability, id=id)

    # 2. Eliminar directamente (hard-delete)
    availability.delete()

    # 3. Retornar vacío con status 204 (sin contenido)
    return 204, None

@products_router.patch("/productos/availability/{id}/", response=ActivityAvailabilityOut)
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


@products_router.get("/productos/", response=list[ProductsMetadataOut])
@paginate(DefaultPagination)
def listar_productos(request, filtros: ProductosFiltro = ProductosFiltro()):
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
            "precio": "precio_unitario",
            "-precio": "-precio_unitario",
            "fecha": "activity__date",
            "-fecha": "-activity__date",
            "nombre": "activity__name",
            "-nombre": "-activity__name",
            "rating": "precio_unitario",  # Placeholder - implementar rating cuando esté disponible
            "-rating": "-precio_unitario",
            "popularidad": "precio_unitario",  # Placeholder - implementar popularidad cuando esté disponible
            "-popularidad": "-precio_unitario",
        }
        qs = qs.order_by(order_map.get(filtros.ordering, "precio_unitario"))

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


@products_router.get("/productos/{id}/", response=ProductsMetadataOut)
def obtener_producto(request, id: int):
    metadata = get_object_or_404(ProductsMetadata.active.select_related("content_type_id"), id=id)
    return serialize_product_metadata(metadata)


@products_router.patch("/productos/{id}/", response=ProductsMetadataOut)
@transaction.atomic
def actualizar_producto(request, id: int, data: ProductsMetadataUpdate):
    metadata = get_object_or_404(
        ProductsMetadata.objects.select_related("content_type_id"), id=id
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


@products_router.delete("/productos/{id}/", response={204: None})
@transaction.atomic
def inactivar_producto(request, id: int):
    metadata = get_object_or_404(ProductsMetadata, id=id)

    metadata.is_active = False
    metadata.deleted_at = timezone.now()
    metadata.save(update_fields=["is_active", "deleted_at"])

    metadata.content.is_active = False
    metadata.content.save(update_fields=["is_active"])

    return 204, None
