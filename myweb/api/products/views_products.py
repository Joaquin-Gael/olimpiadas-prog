from ninja import Router, Query
from .schemas import (
    ProductsMetadataOut, ProductsMetadataCreate, ProductsMetadataUpdate,
    ActivityUpdate, FlightUpdate, LodgmentUpdate, TransportationUpdate,
    ActivityAvailabilityCreate, ActivityAvailabilityOut, ActivityAvailabilityUpdate,
    ActivityCompleteCreate, ActivityMetadataCreate, ActivityAvailabilityCreateNested,
    LodgmentCompleteCreate, LodgmentMetadataCreate, RoomCreateNested, RoomAvailabilityCreateNested,
    TransportationAvailabilityCreate, TransportationAvailabilityOut, TransportationAvailabilityUpdate,
    TransportationCompleteCreate, TransportationMetadataCreate, TransportationAvailabilityCreateNested,
    ProductsMetadataOutLodgmentDetail, RoomAvailabilityCreate, RoomAvailabilityOut, RoomAvailabilityUpdate,
    RoomQuoteOut, CheckAvailabilityOut, FlightOut, LocationListOut, RoomCreate, RoomUpdate, RoomOut,
    RoomDetailOut, RoomWithAvailabilityOut, SerializedHelperMetadata, ItemsPaginationOut
)
from .services.helpers import serialize_product_metadata, serialize_activity_availability, serialize_transportation_availability
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from .models import (
    ProductsMetadata, Suppliers,
    Activities, Flights, Lodgments, Transportation, ActivityAvailability, TransportationAvailability,
    RoomAvailability, Room, Location
)
from django.db.models import Q, F
from ninja.pagination import paginate
from .filters import ProductosFiltro, RoomFilter
from .pagination import DefaultPagination
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta, date, time
from typing import List
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal

from rich import console

console = console.Console()

products_router = Router(tags=["Products"])

@products_router.post("/create/", response=ProductsMetadataOut)
@transaction.atomic
def create_product(request, data: ProductsMetadataCreate):
    supplier = get_object_or_404(Suppliers, id=data.supplier_id)

    # Map product_type to model class
    model_map = {
        "activity": Activities,
        "flight": Flights,
        "lodgment": Lodgments,
        "transportation": Transportation,
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

    # Get ContentType for the model
    content_type = ContentType.objects.get_for_model(Model)

    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=product.id,
        unit_price=data.unit_price,
        currency=getattr(data, 'currency', 'USD')
    )

    return serialize_product_metadata(metadata)


@products_router.post("/activity-complete/", response=ProductsMetadataOut)
@transaction.atomic
def create_complete_activity(request, data: ActivityCompleteCreate, metadata: ActivityMetadataCreate):
    """
    Creates a complete activity with its availabilities in a single operation.
    """
    # 1. Verify that the supplier exists
    supplier = get_object_or_404(Suppliers, id=metadata.supplier_id)
    
    # 2. Create the activity
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
    
    # 3. Create product metadata
    content_type = ContentType.objects.get_for_model(Activities)
    
    metadata_obj = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=activity.id,
        unit_price=metadata.unit_price,
        currency=getattr(metadata, 'currency', 'USD')
    )
    
    # 4. Create availabilities if provided
    created_availabilities = []
    for availability_data in data.availabilities:
        availability = ActivityAvailability(
            activity=activity,
            event_date=availability_data.event_date,
            start_time=availability_data.start_time,
            total_seats=availability_data.total_seats,
            reserved_seats=availability_data.reserved_seats,
            price=availability_data.price,
            currency=availability_data.currency,
            state="active"
        )
        try:
            availability.full_clean()
            availability.save()
            created_availabilities.append(availability)
        except ValidationError as e:
            raise HttpError(422, ", ".join(e.messages))
    
    return serialize_product_metadata(metadata_obj)


@products_router.post("/lodgment-complete/", response=ProductsMetadataOutLodgmentDetail)
@transaction.atomic
def create_complete_lodgment(request, data: LodgmentCompleteCreate, metadata: LodgmentMetadataCreate):
    """
    Creates a complete lodgment with rooms and availabilities in a single operation.
    """
    # 1. Verify that the supplier exists
    supplier = get_object_or_404(Suppliers, id=metadata.supplier_id)
    
    # 2. Create the lodgment
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
    
    lodgment = Lodgments(**lodgment_data)
    
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
    
    # 3. Create product metadata
    content_type = ContentType.objects.get_for_model(Lodgments)
    
    metadata_obj = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=lodgment.id,
        unit_price=metadata.unit_price,
        currency=getattr(metadata, 'currency', 'USD')
    )
    
    # 4. Create rooms and their availabilities
    created_rooms = []
    for room_data in data.rooms:
        room_availabilities = room_data.availabilities
        room_data_dict = room_data.dict(exclude={'availabilities'})
        room = lodgment.rooms.create(**room_data_dict)
        try:
            room.full_clean()
            room.save()
        except ValidationError as e:
            error_messages = []
            for field, errors in e.message_dict.items():
                for error in errors:
                    error_messages.append(f"Room {room.name or room.id} - {field}: {error}")
            error_detail = "; ".join(error_messages)
            raise HttpError(422, error_detail)
        created_rooms.append(room)
        # Crear RoomAvailability con validación previa
        avail_objs = []
        for av_in in room_availabilities:
            availability = RoomAvailability(
                room=room,
                start_date=av_in.start_date,
                end_date=av_in.end_date,
                available_quantity=av_in.available_quantity,
                price_override=av_in.price_override,
                currency=av_in.currency,
                is_blocked=av_in.is_blocked,
                minimum_stay=av_in.minimum_stay
            )
            try:
                availability.full_clean()
                availability.save()
                avail_objs.append(availability)
            except ValidationError as e:
                raise HttpError(422, ", ".join(e.messages))
        RoomAvailability.objects.bulk_create(avail_objs)
    
    return serialize_product_metadata(metadata_obj)


@products_router.post("/transport-complete/", response=ProductsMetadataOut)
@transaction.atomic
def create_complete_transport(request, data: TransportationCompleteCreate, metadata: TransportationMetadataCreate):
    """
    Creates a complete transportation with its availabilities in a single operation.
    """
    # 1. Verify that the supplier exists
    supplier = get_object_or_404(Suppliers, id=metadata.supplier_id)
    
    # 2. Create the transportation
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
    
    # 3. Create product metadata
    content_type = ContentType.objects.get_for_model(Transportation)
    
    metadata_obj = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=content_type,
        object_id=transportation.id,
        unit_price=metadata.unit_price,
        currency=getattr(metadata, 'currency', 'USD')
    )
    
    # 4. Create availabilities if provided
    created_availabilities = []
    for availability_data in data.availabilities:
        availability = TransportationAvailability(
            transportation=transportation,
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
        try:
            availability.full_clean()
            availability.save()
            created_availabilities.append(availability)
        except ValidationError as e:
            raise HttpError(422, ", ".join(e.messages))
    
    return serialize_product_metadata(metadata_obj)


@products_router.post("/{id}/transportation-availability/", response=TransportationAvailabilityOut)
@transaction.atomic
def create_transportation_availability(request, id: int, data: TransportationAvailabilityCreate):
    metadata = get_object_or_404(ProductsMetadata.objects.active().select_related("content_type_id"), id=id)

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


@products_router.get("/{id}/transportation-availability/", response=List[TransportationAvailabilityOut])
def list_transportation_availabilities(request, id: int):
    # 1. Find the product
    metadata = get_object_or_404(
        ProductsMetadata.objects.active().select_related("content_type_id"), id=id
    )

    # 2. Validate type
    if metadata.product_type != "transportation":
        raise HttpError(400, "This product is not a transportation.")

    # 3. Get specific transportation
    transportation = metadata.content

    # 4. Return all availabilities (ordered by date and time)
    availabilities = transportation.availabilities.order_by("departure_date", "departure_time").all()
    return [serialize_transportation_availability(av) for av in availabilities]


@products_router.delete("/transportation-availability/{id}/", response={204: None})
@transaction.atomic
def delete_transportation_availability(request, id: int):
    # 1. Find the availability
    availability = get_object_or_404(TransportationAvailability, id=id)

    # 2. Delete directly (hard-delete)
    availability.delete()

    # 3. Return empty with status 204 (no content)
    return 204, None


@products_router.patch("/transportation-availability/{id}/", response=TransportationAvailabilityOut)
@transaction.atomic
def update_transportation_availability(request, id: int, data: TransportationAvailabilityUpdate):
    availability = get_object_or_404(TransportationAvailability, id=id)

    # Cross validations
    if data.reserved_seats is not None:
        total = data.total_seats if data.total_seats is not None else availability.total_seats
        if data.reserved_seats > total:
            raise HttpError(422, "Reserved seats cannot exceed total seats.")

    if data.departure_date is not None and data.departure_date < datetime.now().date():
        raise HttpError(422, "Departure date cannot be in the past.")

    # Apply changes
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(availability, attr, value)

    availability.full_clean()
    availability.save()

    return serialize_transportation_availability(availability)


@products_router.post("/{id}/availability/", response=ActivityAvailabilityOut)
@transaction.atomic
def create_availability(request, id: int, data: ActivityAvailabilityCreate):
    metadata = get_object_or_404(ProductsMetadata.objects.active().select_related("content_type_id"), id=id)

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

@products_router.get("/{id}/availability/", response=List[ActivityAvailabilityOut])
def list_availabilities(request, id: int):
    # 1. Find the product
    metadata = get_object_or_404(
        ProductsMetadata.objects.active().select_related("content_type_id"), id=id
    )

    # 2. Validate type
    if metadata.product_type != "activity":
        raise HttpError(400, "This product is not an activity.")

    # 3. Get specific activity
    activity = metadata.content

    # 4. Return all availabilities (ordered by date and time)
    availabilities = activity.availabilities.order_by("event_date", "start_time").all()
    return [serialize_activity_availability(av) for av in availabilities]

@products_router.delete("/availability/{id}/", response={204: None})
@transaction.atomic
def delete_availability(request, id: int):
    # 1. Find the availability
    availability = get_object_or_404(ActivityAvailability, id=id)

    # 2. Delete directly (hard-delete)
    availability.delete()

    # 3. Return empty with status 204 (no content)
    return 204, None

@products_router.patch("/availability/{id}/", response=ActivityAvailabilityOut)
@transaction.atomic
def update_availability(request, id: int, data: ActivityAvailabilityUpdate):
    availability = get_object_or_404(ActivityAvailability, id=id)

    # Cross validations
    if data.reserved_seats is not None:
        total = data.total_seats if data.total_seats is not None else availability.total_seats
        if data.reserved_seats > total:
            raise HttpError(422, "Reserved seats cannot exceed total seats.")

    if data.event_date is not None and data.event_date < datetime.now().date():
        raise HttpError(422, "Event date cannot be in the past.")

    # Apply changes
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(availability, attr, value)

    availability.full_clean()
    availability.save()

    return serialize_activity_availability(availability)


@products_router.get("/test/", response={200: dict})
def test_products_endpoint(request):
    """
    Endpoint de prueba para diagnosticar problemas con productos
    """
    try:
        # Contar productos activos
        total_active = ProductsMetadata.objects.active().count()
        
        # Contar por tipo
        activity_count = ProductsMetadata.objects.active().filter(activity__isnull=False).count()
        flight_count = ProductsMetadata.objects.active().filter(flights__isnull=False).count()
        lodgment_count = ProductsMetadata.objects.active().filter(lodgment__isnull=False).count()
        transportation_count = ProductsMetadata.objects.active().filter(transportation__isnull=False).count()
        
        # Probar available_only
        available_count = ProductsMetadata.objects.active().available_only().count()
        
        # Verificar productos con problemas
        products_with_issues = []
        for metadata in ProductsMetadata.objects.active()[:5]:  # Solo los primeros 5
            try:
                serialize_product_metadata(metadata)
            except Exception as e:
                products_with_issues.append({
                    "id": metadata.id,
                    "product_type": metadata.product_type,
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "total_active_products": total_active,
            "by_type": {
                "activity": activity_count,
                "flight": flight_count,
                "lodgment": lodgment_count,
                "transportation": transportation_count
            },
            "available_products": available_count,
            "products_with_issues": products_with_issues,
            "message": "Diagnóstico completado"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Error en el diagnóstico"
        }


@products_router.get("/all/", response={200: List[ProductsMetadataOut]})
@paginate(DefaultPagination)
def list_all_products(request):
    """
    Lists all active products without availability filters
    """
    # Solo filtrar por productos activos, sin filtros de disponibilidad
    data = ProductsMetadata.objects.active().select_related(
        'supplier', 'content_type_id'
    ).prefetch_related(
        'activity__location',
        'flights__origin',
        'flights__destination', 
        'lodgment__location',
        'lodgment__rooms',
        'transportation__origin',
        'transportation__destination'
    )
    
    serialized_list = []
    for metadata in data:
        try:
            serialized_data = serialize_product_metadata(metadata)
            serialized_list.append(serialized_data)
        except Exception as e:
            console.print(f"Error serializando producto {metadata.id}: {str(e)}")
            continue
    
    console.print(f"Productos serializados: {len(serialized_list)}")
    return serialized_list


@products_router.get("/", response={200: ItemsPaginationOut})
#@paginate(DefaultPagination)
def list_products(request, limit: int = Query(100), offset: int = Query(0)):
    """
    Lists all products with advanced filters and pagination
    """
    # Optimizar consultas con select_related y prefetch_related
    data = ProductsMetadata.objects.active().available_only().select_related(
        'supplier', 'content_type_id'
    ).prefetch_related(
        'activity__location',
        'flights__origin',
        'flights__destination', 
        'lodgment__location',
        'lodgment__rooms',
        'transportation__origin',
        'transportation__destination'
    )
    
    serialized_list = []
    for metadata in data:
        try:
            serialized_data = serialize_product_metadata(metadata)
            # No duplicar unit_price ya que ya está en serialized_data
            serialized_list.append(serialized_data)
        except Exception as e:
            console.print(f"Error serializando producto {metadata.id}: {str(e)}")
            # Continuar con el siguiente producto en lugar de fallar completamente
            continue
    
    console.print(f"Productos serializados: {len(serialized_list)}")
    filtered_serialized_list = serialized_list[offset:limit]
    return {"items": filtered_serialized_list, "count": len(filtered_serialized_list)}


@products_router.get("/{id}/", response=ProductsMetadataOut)
def get_product(request, id: int):
    metadata = get_object_or_404(ProductsMetadata.objects.active().select_related("content_type_id"), id=id)
    return serialize_product_metadata(metadata)


@products_router.patch("/{id}/", response=ProductsMetadataOut)
@transaction.atomic
def update_product(request, id: int, data: ProductsMetadataUpdate):
    metadata = get_object_or_404(ProductsMetadata.objects.active().select_related("content_type_id"), id=id)
    product = metadata.content

    # Actualizar campos de metadata
    if data.unit_price is not None:
        if data.unit_price < 0:
            raise HttpError(400, "The price cannot be negative")
        metadata.unit_price = data.unit_price
    if data.supplier_id is not None:
        metadata.supplier_id = data.supplier_id

    # Actualizar producto principal
    if data.product is not None:
        product_fields = data.product.dict(exclude_unset=True, exclude={"rooms", "availabilities", "flights", "transportations"})
        for attr, value in product_fields.items():
            if hasattr(product, attr):
                setattr(product, attr, value)
        try:
            product.full_clean()
            product.save()
        except ValidationError as e:
            raise HttpError(422, str(e))

    # PATCH anidado para alojamientos
    if hasattr(data, "rooms") and data.rooms:
        for room_data in data.rooms:
            room = product.rooms.get(pk=room_data.id)
            for f, v in room_data.dict(exclude_unset=True, exclude={"id"}).items():
                setattr(room, f, v)
            room.full_clean()
            room.save()
    if hasattr(data, "availabilities") and data.availabilities:
        # Para alojamientos y actividades
        if hasattr(product, "availabilities"):
            for av_data in data.availabilities:
                av = product.availabilities.get(pk=av_data.id)
                for f, v in av_data.dict(exclude_unset=True, exclude={"id"}).items():
                    setattr(av, f, v)
                av.full_clean()
                av.save()
        elif hasattr(product, "rooms"):
            # Para RoomAvailability en Lodgment
            for av_data in data.availabilities:
                for room in product.rooms.all():
                    try:
                        av = room.availabilities.get(pk=av_data.id)
                        for f, v in av_data.dict(exclude_unset=True, exclude={"id"}).items():
                            setattr(av, f, v)
                        av.full_clean()
                        av.save()
                        break
                    except room.availabilities.model.DoesNotExist:
                        continue
    # PATCH anidado para vuelos
    if hasattr(data, "flights") and data.flights:
        for flight_data in data.flights:
            flight = product.flights.get(pk=flight_data.id)
            for f, v in flight_data.dict(exclude_unset=True, exclude={"id"}).items():
                setattr(flight, f, v)
            flight.full_clean()
            flight.save()
    # PATCH anidado para transportes
    if hasattr(data, "transportations") and data.transportations:
        for t_data in data.transportations:
            t = product.transportation.get(pk=t_data.id)
            for f, v in t_data.dict(exclude_unset=True, exclude={"id"}).items():
                setattr(t, f, v)
            t.full_clean()
            t.save()

    metadata.save(update_fields=["unit_price", "supplier_id"])
    return serialize_product_metadata(metadata)


@products_router.delete("/{id}/", response={204: None})
@transaction.atomic
def deactivate_product(request, id: int):
    metadata = get_object_or_404(ProductsMetadata.objects.active(), id=id)
    metadata.is_active = False
    metadata.deleted_at = timezone.now()
    metadata.save()
    
    # También desactivar el producto relacionado
    product = metadata.content
    if hasattr(product, 'is_active'):
        product.is_active = False
        product.save(update_fields=['is_active'])
    
    return 204, None


@products_router.get("/search/advanced/", response=list[ProductsMetadataOut])
@paginate(DefaultPagination)
def advanced_search(request, filters: ProductosFiltro = ProductosFiltro()):
    """
    Advanced search with combined filters and more sophisticated logic
    """
    return ProductsMetadata.objects.active().apply_filters(filters)


@products_router.get("/search/quick/", response=list[ProductsMetadataOut])
def quick_search(request, q: str, limit: int = 10):
    """
    Quick text search with result limit
    """
    qs = ProductsMetadata.objects.active().select_related(
        "supplier", "content_type_id"
    ).prefetch_related(
        "activity", "flight", "lodgment", "transportation"
    )
    
    # Simple text search
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


@products_router.get("/stats/filters/")
def get_filter_stats(request):
    """
    Gets statistics to help with filters
    """
    from django.db.models import Count, Min, Max, Avg
    
    stats = {
        "price_range": {
            "min": ProductsMetadata.objects.active().aggregate(Min('unit_price'))['unit_price__min'] or 0,
            "max": ProductsMetadata.objects.active().aggregate(Max('unit_price'))['unit_price__max'] or 0,
            "avg": ProductsMetadata.objects.active().aggregate(Avg('unit_price'))['unit_price__avg'] or 0,
        },
        "product_types": {
            "activity": ProductsMetadata.objects.active().filter(product_type="activity").count(),
            "flight": ProductsMetadata.objects.active().filter(product_type="flight").count(),
            "lodgment": ProductsMetadata.objects.active().filter(product_type="lodgment").count(),
            "transportation": ProductsMetadata.objects.active().filter(product_type="transportation").count(),
        },
        "locations": {
            "total": Location.objects.count(),
        },
        "suppliers": {
            "total": Suppliers.active.count(),
        }
    }
    
    return stats

# ──────────────────────────────────────────────────────────────
# ENDPOINTS TO MANAGE FLIGHT AVAILABILITY
# ──────────────────────────────────────────────────────────────

@products_router.patch("/{id}/flight-availability/", response=ProductsMetadataOut)
@transaction.atomic
def update_flight_availability(request, id: int, available_seats: int):
    """
    Updates the seat availability of a flight
    """
    metadata = get_object_or_404(ProductsMetadata.objects.active().select_related("content_type_id"), id=id)

    if metadata.product_type != "flight":
        raise HttpError(400, "This product is not a flight.")

    flight = metadata.content

    if not flight.is_active:
        raise HttpError(400, "The flight is inactive.")

    if available_seats < 0:
        raise HttpError(422, "Available seats cannot be negative.")

    if available_seats > 500:
        raise HttpError(422, "Available seats cannot exceed 500.")

    # Update availability
    flight.available_seats = available_seats
    
    try:
        flight.full_clean()
        flight.save()
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, error_detail)

    return serialize_product_metadata(metadata)


@products_router.get("/{id}/flight-availability/")
def get_flight_availability(request, id: int):
    """
    Gets the current availability of a flight
    """
    metadata = get_object_or_404(ProductsMetadata.objects.active().select_related("content_type_id"), id=id)
    if metadata.product_type != "flight":
        raise HttpError(400, "This product is not a flight.")
    flight = metadata.content
    return FlightOut.from_orm(flight)


# ──────────────────────────────────────────────────────────────
# ENDPOINTS TO MANAGE ROOM AVAILABILITY
# ──────────────────────────────────────────────────────────────

@products_router.post("/room-availability/", response=RoomAvailabilityOut)
@transaction.atomic
def create_room_availability(request, data: RoomAvailabilityCreate):
    """
    Creates a new availability for a room
    """
    # Verify that the room exists and is active
    room = get_object_or_404(Room, id=data.room_id, is_active=True)
    
    # Verify that the lodgment is active
    if not room.lodgment.is_active:
        raise HttpError(400, "The lodgment is inactive.")

    # Validate that there is no date overlap
    existing_availability = room.availabilities.filter(
        start_date__lt=data.end_date,
        end_date__gt=data.start_date
    ).first()
    
    if existing_availability:
        raise HttpError(422, f"Date range overlaps with existing availability: {existing_availability.start_date} to {existing_availability.end_date}")

    # Create the availability
    availability = room.availabilities.create(
        start_date=data.start_date,
        end_date=data.end_date,
        available_quantity=data.available_quantity,
        price_override=data.price_override,
        currency=data.currency,
        is_blocked=data.is_blocked,
        minimum_stay=data.minimum_stay
    )

    return RoomAvailabilityOut.from_orm(availability)


@products_router.get("/room-availability/{id}/", response=RoomAvailabilityOut)
def get_room_availability(request, id: int):
    """
    Gets a specific room availability
    """
    availability = get_object_or_404(RoomAvailability, id=id)
    
    return RoomAvailabilityOut.from_orm(availability)


@products_router.get("/room/{room_id}/availabilities/", response=List[RoomAvailabilityOut])
def list_room_availabilities(request, room_id: int):
    """
    Lists all availabilities of a specific room
    """
    room = get_object_or_404(Room, id=room_id, is_active=True)
    
    availabilities = room.availabilities.order_by("start_date").all()
    
    return [RoomAvailabilityOut.from_orm(av) for av in availabilities]


@products_router.patch("/room-availability/{id}/", response=RoomAvailabilityOut)
@transaction.atomic
def update_room_availability(request, id: int, data: RoomAvailabilityUpdate):
    """
    Updates a room availability
    """
    availability = get_object_or_404(RoomAvailability, id=id)

    # Date validations
    if data.start_date is not None and data.start_date < datetime.now().date():
        raise HttpError(422, "Start date cannot be in the past.")

    if data.end_date is not None:
        start_date = data.start_date if data.start_date is not None else availability.start_date
        if data.end_date <= start_date:
            raise HttpError(422, "End date must be after start date.")

    # Check overlap if dates are changed
    if data.start_date is not None or data.end_date is not None:
        new_start = data.start_date if data.start_date is not None else availability.start_date
        new_end = data.end_date if data.end_date is not None else availability.end_date
        
        existing_availability = availability.room.availabilities.filter(
            ~Q(id=availability.id),  # Exclude current availability
            start_date__lt=new_end,
            end_date__gt=new_start
        ).first()
        
        if existing_availability:
            raise HttpError(422, f"Date range overlaps with existing availability: {existing_availability.start_date} to {existing_availability.end_date}")

    # Apply changes
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(availability, attr, value)

    try:
        availability.full_clean()
        availability.save()
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, error_detail)

    return RoomAvailabilityOut.from_orm(availability)


@products_router.delete("/room-availability/{id}/", response={204: None})
@transaction.atomic
def delete_room_availability(request, id: int):
    """
    Deletes a room availability
    """
    availability = get_object_or_404(RoomAvailability, id=id)
    
    # Verify that there are no active reservations (this would be implemented when the reservation system is available)
    # For now, just delete directly
    
    availability.delete()
    
    return 204, None


@products_router.get("/lodgment/{lodgment_id}/rooms/availabilities/", response=List[dict])
def list_lodgment_room_availabilities(request, lodgment_id: int, start_date: date = None, end_date: date = None):
    """
    Lists all room availabilities of a lodgment
    Optionally filters by date range
    """
    lodgment = get_object_or_404(Lodgments, id=lodgment_id, is_active=True)
    
    rooms = lodgment.rooms.filter(is_active=True)
    
    result = []
    for room in rooms:
        availabilities = room.availabilities.all()
        
        # Filter by dates if provided
        if start_date:
            availabilities = availabilities.filter(end_date__gte=start_date)
        if end_date:
            availabilities = availabilities.filter(start_date__lte=end_date)
        
        availabilities = availabilities.order_by("start_date")
        
        room_data = {
            "room_id": room.id,
            "room_type": room.room_type,
            "name": room.name,
            "capacity": room.capacity,
            "base_price_per_night": float(room.base_price_per_night),
            "currency": room.currency,
            "availabilities": [
                {
                    "id": av.id,
                    "start_date": av.start_date,
                    "end_date": av.end_date,
                    "available_quantity": av.available_quantity,
                    "price_override": float(av.price_override) if av.price_override else None,
                    "is_blocked": av.is_blocked,
                    "minimum_stay": av.minimum_stay,
                    "effective_price": float(av.effective_price)
                }
                for av in availabilities
            ]
        }
        result.append(room_data)
    
    return result


@products_router.get("/room/{room_id}/quote/", response=RoomQuoteOut)
def quote_room(request, room_id: int, start_date: date, end_date: date, qty: int = 1):
    if start_date >= end_date:
        raise HttpError(422, "start_date debe ser < end_date")
    if qty <= 0:
        raise HttpError(422, "qty debe ser positivo")

    try:
        av = RoomAvailability.objects.select_for_update().get(
            room_id=room_id,
            start_date__lte=start_date,
            end_date__gte=end_date,
            is_blocked=False,
        )
    except RoomAvailability.DoesNotExist:
        raise HttpError(404, "No hay disponibilidad para ese rango")

    nights = (end_date - start_date).days
    if nights < av.minimum_stay:
        raise HttpError(422, f"Mínimo {av.minimum_stay} noche(s)")

    if av.available_quantity < qty:
        return 409, {"remaining": av.available_quantity}

    unit = av.effective_price
    subtotal = unit * nights * qty
    taxes = subtotal * Decimal("0.21")  # Cambia si tienes otro IVA
    total = subtotal + taxes

    return RoomQuoteOut(
        unit_price=float(unit),
        nights=nights,
        rooms=qty,
        subtotal=float(subtotal),
        taxes=float(taxes),
        total_price=float(total),
        currency=av.currency,
        availability_id=av.id
    )

@products_router.get("/{metadata_id}/check/", response=CheckAvailabilityOut)
def check_activity(request, metadata_id: int, qty: int, date: date, start_time: time):
    """Verifica disponibilidad de stock para una actividad usando el servicio mejorado."""
    from .models import ActivityAvailability
    from .services.stock_services import check_activity_stock, InvalidQuantityError, ProductNotFoundError
    
    try:
        # Buscar la disponibilidad de la actividad
        av = ActivityAvailability.objects.get(
            activity__product_metadata_id=metadata_id,
            event_date=date,
            start_time=start_time,
            state="active",
        )
        
        # Usar el servicio mejorado para verificar stock
        stock_info = check_activity_stock(av.id, qty)
        
        return CheckAvailabilityOut(
            remaining=stock_info['available'],
            enough=stock_info['sufficient'],
            unit_price=float(av.price),
            currency=av.currency,
            availability_id=av.id,
        )
        
    except InvalidQuantityError as e:
        raise HttpError(422, str(e))
    except ProductNotFoundError as e:
        raise HttpError(404, str(e))
    except ActivityAvailability.DoesNotExist:
        raise HttpError(404, "No existe disponibilidad para la fecha y horario especificados")
    except Exception as e:
        raise HttpError(500, f"Error al verificar disponibilidad: {str(e)}")

@products_router.get("/{metadata_id}/transport/check/", response=CheckAvailabilityOut)
def check_transport(request, metadata_id: int, qty: int, date: date, time: time):
    """Verifica disponibilidad de stock para transporte usando el servicio mejorado."""
    from .models import TransportationAvailability
    from .services.stock_services import check_transportation_stock, InvalidQuantityError, ProductNotFoundError
    
    try:
        # Buscar la disponibilidad de transporte
        av = TransportationAvailability.objects.get(
            transportation__product_metadata_id=metadata_id,
            departure_date=date,
            departure_time=time,
        )
        
        # Usar el servicio mejorado para verificar stock
        stock_info = check_transportation_stock(av.id, qty)
        
        return CheckAvailabilityOut(
            remaining=stock_info['available'],
            enough=stock_info['sufficient'],
            unit_price=float(av.price),
            currency=av.currency,
            availability_id=av.id,
        )
        
    except InvalidQuantityError as e:
        raise HttpError(422, str(e))
    except ProductNotFoundError as e:
        raise HttpError(404, str(e))
    except TransportationAvailability.DoesNotExist:
        raise HttpError(404, "No existe disponibilidad para la fecha y horario especificados")
    except Exception as e:
        raise HttpError(500, f"Error al verificar disponibilidad: {str(e)}")

@products_router.get("/{metadata_id}/flight/check/", response=CheckAvailabilityOut)
def check_flight(request, metadata_id: int, qty: int):
    """Verifica disponibilidad de stock para un vuelo usando el servicio mejorado."""
    from .models import Flights, ProductsMetadata
    from .services.stock_services import check_flight_stock, InvalidQuantityError, ProductNotFoundError
    
    try:
        # Buscar el vuelo y metadata
        flight = Flights.objects.get(product_metadata_id=metadata_id)
        meta = ProductsMetadata.objects.get(id=metadata_id)
        
        # Usar el servicio mejorado para verificar stock
        stock_info = check_flight_stock(flight.id, qty)
        
        return CheckAvailabilityOut(
            remaining=stock_info['available'],
            enough=stock_info['sufficient'],
            unit_price=float(meta.unit_price),
            currency=meta.currency,
            availability_id=flight.id,
        )
        
    except InvalidQuantityError as e:
        raise HttpError(422, str(e))
    except ProductNotFoundError as e:
        raise HttpError(404, str(e))
    except Flights.DoesNotExist:
        raise HttpError(404, "No existe el vuelo especificado")
    except ProductsMetadata.DoesNotExist:
        raise HttpError(404, "No existe metadata para el producto")
    except Exception as e:
        raise HttpError(500, f"Error al verificar disponibilidad: {str(e)}")

@products_router.get("/room/{room_id}/check/", response=CheckAvailabilityOut)
def check_room(request, room_id: int, qty: int, start_date: date, end_date: date):
    """Verifica disponibilidad de stock para habitaciones usando el servicio mejorado."""
    from .models import RoomAvailability
    from .services.stock_services import check_room_stock, InvalidQuantityError, ProductNotFoundError
    
    if start_date >= end_date:
        raise HttpError(422, "start_date debe ser anterior a end_date")
    
    try:
        # Buscar la disponibilidad de la habitación
        av = RoomAvailability.objects.get(
            room_id=room_id,
            start_date__lte=start_date,
            end_date__gte=end_date,
            is_blocked=False,
        )
        
        # Usar el servicio mejorado para verificar stock
        stock_info = check_room_stock(av.id, qty)
        
        return CheckAvailabilityOut(
            remaining=stock_info['available'],
            enough=stock_info['sufficient'],
            unit_price=float(av.effective_price),
            currency=av.currency,
            availability_id=av.id,
        )
        
    except InvalidQuantityError as e:
        raise HttpError(422, str(e))
    except ProductNotFoundError as e:
        raise HttpError(404, str(e))
    except RoomAvailability.DoesNotExist:
        raise HttpError(404, "No existe disponibilidad para el rango de fechas especificado")
    except Exception as e:
        raise HttpError(500, f"Error al verificar disponibilidad: {str(e)}")
    
# ─────────────────────────────────────────────
# NUEVOS ENDPOINTS PARA VALIDACIÓN DE STOCK
# ─────────────────────────────────────────────

@products_router.post("/products/stock/validate-bulk/")
def validate_bulk_stock(request, reservations: List[dict]):
    """
    Valida múltiples reservas de stock antes de ejecutarlas.
    Útil para verificar disponibilidad de paquetes completos.
    """
    from .services.stock_services import validate_bulk_stock_reservation
    
    try:
        validation_result = validate_bulk_stock_reservation(reservations)
        return {
            'valid': validation_result['valid'],
            'errors': validation_result['errors'],
            'warnings': validation_result['warnings'],
            'valid_reservations': len(validation_result['reservations']),
            'total_reservations': len(reservations)
        }
    except Exception as e:
        raise HttpError(500, f"Error al validar reservas: {str(e)}")

@products_router.get("/products/stock/summary/{product_type}/{product_id}/")
def get_stock_summary(request, product_type: str, product_id: int):
    """
    Obtiene un resumen detallado del stock actual de un producto.
    """
    from .services.stock_services import get_stock_summary, ProductNotFoundError
    
    try:
        summary = get_stock_summary(product_type, product_id)
        return summary
    except ProductNotFoundError as e:
        raise HttpError(404, str(e))
    except ValueError as e:
        raise HttpError(422, str(e))
    except Exception as e:
        raise HttpError(500, f"Error al obtener resumen de stock: {str(e)}")

@products_router.get("/locations/", response=List[LocationListOut])
def list_locations(request, is_active: bool = True, type: str = None, country: str = None, search: str = None):
    qs = Location.objects.all()
    if is_active:
        qs = qs.filter(is_active=True)
    if type:
        qs = qs.filter(type=type)
    if country:
        qs = qs.filter(country__iexact=country)
    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(city__icontains=search) |
            Q(state__icontains=search) |
            Q(code__icontains=search)
        )
    return [
        LocationListOut(
            id=loc.id,
            name=loc.name,
            country=loc.country,
            state=loc.state,
            city=loc.city,
            code=loc.code,
            type=loc.type,
            parent_id=loc.parent_id,
            latitude=float(loc.latitude) if loc.latitude is not None else None,
            longitude=float(loc.longitude) if loc.longitude is not None else None,
            is_active=loc.is_active
        )
        for loc in qs.order_by("country", "state", "city", "name")
    ]

# ──────────────────────────────────────────────────────────────
# ENDPOINTS CRUD PARA HABITACIONES
# ──────────────────────────────────────────────────────────────

@products_router.post("/rooms/", response=RoomOut)
@transaction.atomic
def create_room(request, data: RoomCreate):
    """
    Crea una nueva habitación independiente
    """
    # 1. Verificar que el alojamiento existe y está activo
    lodgment = get_object_or_404(Lodgments, id=data.lodgment_id, is_active=True)
    
    # 2. Crear la habitación
    room_data = {
        "lodgment": lodgment,
        "room_type": data.room_type,
        "name": data.name,
        "description": data.description,
        "capacity": data.capacity,
        "has_private_bathroom": data.has_private_bathroom,
        "has_balcony": data.has_balcony,
        "has_air_conditioning": data.has_air_conditioning,
        "has_wifi": data.has_wifi,
        "base_price_per_night": Decimal(str(data.base_price_per_night)),
        "currency": data.currency,
    }
    
    room = Room(**room_data)
    
    # 3. Validar y guardar
    try:
        room.full_clean()
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, error_detail)
    
    room.save()
    
    return serialize_room(room)


@products_router.get("/rooms/", response=List[RoomOut])
@paginate(DefaultPagination)
def list_rooms(request, filters: RoomFilter = RoomFilter()):
    """
    Lista todas las habitaciones con filtros y paginación
    """
    qs = Room.objects.select_related("lodgment")
    
    # Aplicar filtros
    if filters.lodgment_id:
        qs = qs.filter(lodgment_id=filters.lodgment_id)
    
    if filters.room_type:
        qs = qs.filter(room_type=filters.room_type)
    
    if filters.capacity_min is not None:
        qs = qs.filter(capacity__gte=filters.capacity_min)
    
    if filters.capacity_max is not None:
        qs = qs.filter(capacity__lte=filters.capacity_max)
    
    if filters.price_min is not None:
        qs = qs.filter(base_price_per_night__gte=Decimal(str(filters.price_min)))
    
    if filters.price_max is not None:
        qs = qs.filter(base_price_per_night__lte=Decimal(str(filters.price_max)))
    
    if filters.has_private_bathroom is not None:
        qs = qs.filter(has_private_bathroom=filters.has_private_bathroom)
    
    if filters.has_balcony is not None:
        qs = qs.filter(has_balcony=filters.has_balcony)
    
    if filters.has_air_conditioning is not None:
        qs = qs.filter(has_air_conditioning=filters.has_air_conditioning)
    
    if filters.has_wifi is not None:
        qs = qs.filter(has_wifi=filters.has_wifi)
    
    if filters.is_active is not None:
        qs = qs.filter(is_active=filters.is_active)
    else:
        # Por defecto, mostrar solo habitaciones activas
        qs = qs.filter(is_active=True)
    
    if filters.currency:
        qs = qs.filter(currency__iexact=filters.currency)
    
    if filters.search:
        qs = qs.filter(
            Q(name__icontains=filters.search) |
            Q(description__icontains=filters.search) |
            Q(lodgment__name__icontains=filters.search)
        )
    
    # Ordenamiento por defecto
    qs = qs.order_by("lodgment__name", "room_type", "name")
    
    return [serialize_room(room) for room in qs]


@products_router.get("/rooms/{id}/", response=RoomDetailOut)
def get_room(request, id: int):
    """
    Obtiene una habitación específica con sus disponibilidades
    """
    room = get_object_or_404(
        Room.objects.select_related("lodgment").prefetch_related("availabilities"),
        id=id
    )
    
    return serialize_room_with_availability(room)


@products_router.patch("/rooms/{id}/", response=RoomOut)
@transaction.atomic
def update_room(request, id: int, data: RoomUpdate):
    """
    Actualiza una habitación existente
    """
    room = get_object_or_404(Room, id=id)
    
    # Obtener datos de actualización
    update_data = data.dict(exclude_unset=True)
    
    # Manejar lodgment_id de forma especial
    if 'lodgment_id' in update_data:
        lodgment_id = update_data.pop('lodgment_id')
        lodgment = get_object_or_404(Lodgments, id=lodgment_id, is_active=True)
        room.lodgment = lodgment
    
    # Manejar conversiones de tipos específicos
    if 'base_price_per_night' in update_data:
        update_data['base_price_per_night'] = Decimal(str(update_data['base_price_per_night']))
    
    # Aplicar otros cambios
    for attr, value in update_data.items():
        if hasattr(room, attr):
            setattr(room, attr, value)
    
    # Validar y guardar
    try:
        room.full_clean()
        room.save()
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, error_detail)
    
    return serialize_room(room)


@products_router.delete("/rooms/{id}/", response={204: None})
@transaction.atomic
def delete_room(request, id: int):
    """
    Elimina una habitación (soft delete - desactiva)
    """
    room = get_object_or_404(Room, id=id)
    
    # Verificar que no tenga reservas activas (esto se implementaría cuando tengas el sistema de reservas)
    # Por ahora, solo desactivamos la habitación
    
    room.is_active = False
    room.save(update_fields=['is_active'])
    
    return 204, None


@products_router.get("/rooms/{id}/with-availability/", response=RoomWithAvailabilityOut)
def get_room_with_availability(request, id: int):
    """
    Obtiene una habitación con información de disponibilidad y precio efectivo
    """
    room = get_object_or_404(
        Room.objects.select_related("lodgment").prefetch_related("availabilities"),
        id=id
    )
    
    return serialize_room_with_availability(room)


@products_router.get("/lodgments/{lodgment_id}/rooms/", response=List[RoomOut])
def list_lodgment_rooms(request, lodgment_id: int, is_active: bool = None):
    """
    Lista todas las habitaciones de un alojamiento específico
    """
    lodgment = get_object_or_404(Lodgments, id=lodgment_id, is_active=True)
    
    rooms = lodgment.rooms.select_related("lodgment")
    
    # Aplicar filtro de estado si se especifica
    if is_active is not None:
        rooms = rooms.filter(is_active=is_active)
    else:
        # Por defecto, mostrar solo habitaciones activas
        rooms = rooms.filter(is_active=True)
    
    rooms = rooms.order_by("room_type", "name")
    
    return [serialize_room(room) for room in rooms]


