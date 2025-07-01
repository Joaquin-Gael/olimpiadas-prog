from ninja import Router
from .schemas import (
    ProductsMetadataOut, ProductsMetadataCreate, ProductsMetadataUpdate,
    ActivityUpdate, FlightUpdate, LodgmentUpdate, TransportationUpdate,
    ActivityAvailabilityCreate, ActivityAvailabilityOut, ActivityAvailabilityUpdate,
    ActivityCompleteCreate, ActivityMetadataCreate, ActivityAvailabilityCreateNested,
    LodgmentCompleteCreate, LodgmentMetadataCreate, RoomCreateNested, RoomAvailabilityCreateNested,
    TransportationAvailabilityCreate, TransportationAvailabilityOut, TransportationAvailabilityUpdate,
    TransportationCompleteCreate, TransportationMetadataCreate, TransportationAvailabilityCreateNested,
    ProductsMetadataOutLodgmentDetail, RoomAvailabilityCreate, RoomAvailabilityOut, RoomAvailabilityUpdate,
    RoomQuoteOut, CheckAvailabilityOut
)
from .services.helpers import serialize_product_metadata, serialize_activity_availability, serialize_transportation_availability
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from .models import (
    ProductsMetadata, Suppliers,
    Activities, Flights, Lodgment, Transportation, ActivityAvailability, TransportationAvailability,
    RoomAvailability, Room, Location
)
from django.db.models import Q, F
from ninja.pagination import paginate
from .filters import ProductosFiltro
from .pagination import DefaultPagination
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta, date, time
from typing import List
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal

products_router = Router(tags=["Products"])

@products_router.post("/products/create/", response=ProductsMetadataOut)
@transaction.atomic
def create_product(request, data: ProductsMetadataCreate):
    supplier = get_object_or_404(Suppliers, id=data.supplier_id)

    # Map product_type to model class
    model_map = {
        "activity": Activities,
        "flight": Flights,
        "lodgment": Lodgment,
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


@products_router.post("/products/activity-complete/", response=ProductsMetadataOut)
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
    
    # 3. Create product metadata
    content_type = ContentType.objects.get_for_model(Lodgment)
    
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
        # Extract availabilities before creating the room
        room_availabilities = room_data.availabilities
        room_data_dict = room_data.dict(exclude={'availabilities'})
        
        # Create the room
        room = lodgment.rooms.create(**room_data_dict)
        created_rooms.append(room)
        
        # Create room availabilities
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
    # 1. Find the product
    metadata = get_object_or_404(
        ProductsMetadata.active.select_related("content_type_id"), id=id
    )

    # 2. Validate type
    if metadata.product_type != "transportation":
        raise HttpError(400, "This product is not a transportation.")

    # 3. Get specific transportation
    transportation = metadata.content

    # 4. Return all availabilities (ordered by date and time)
    availabilities = transportation.availabilities.order_by("departure_date", "departure_time").all()
    return [serialize_transportation_availability(av) for av in availabilities]


@products_router.delete("/products/transportation-availability/{id}/", response={204: None})
@transaction.atomic
def delete_transportation_availability(request, id: int):
    # 1. Find the availability
    availability = get_object_or_404(TransportationAvailability, id=id)

    # 2. Delete directly (hard-delete)
    availability.delete()

    # 3. Return empty with status 204 (no content)
    return 204, None


@products_router.patch("/products/transportation-availability/{id}/", response=TransportationAvailabilityOut)
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
    # 1. Find the product
    metadata = get_object_or_404(
        ProductsMetadata.active.select_related("content_type_id"), id=id
    )

    # 2. Validate type
    if metadata.product_type != "activity":
        raise HttpError(400, "This product is not an activity.")

    # 3. Get specific activity
    activity = metadata.content

    # 4. Return all availabilities (ordered by date and time)
    availabilities = activity.availabilities.order_by("event_date", "start_time").all()
    return [serialize_activity_availability(av) for av in availabilities]

@products_router.delete("/products/availability/{id}/", response={204: None})
@transaction.atomic
def delete_availability(request, id: int):
    # 1. Find the availability
    availability = get_object_or_404(ActivityAvailability, id=id)

    # 2. Delete directly (hard-delete)
    availability.delete()

    # 3. Return empty with status 204 (no content)
    return 204, None

@products_router.patch("/products/availability/{id}/", response=ActivityAvailabilityOut)
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


@products_router.get("/products/", response=list[ProductsMetadataOut])
@paginate(DefaultPagination)
def list_products(request, filters: ProductosFiltro = ProductosFiltro()):
    """
    Lists all products with advanced filters and pagination
    """
    qs = ProductsMetadata.active.select_related(
        "supplier", "content_type_id"
    ).prefetch_related(
        "activity", "flight", "lodgment", "transportation"
    )

    # ──────────────────────────────────────────────────────────────
    # BASIC FILTERS
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
    # PRICE FILTERS
    # ──────────────────────────────────────────────────────────────
    if filters.unit_price_min is not None:
        qs = qs.filter(unit_price__gte=filters.unit_price_min)
    if filters.unit_price_max is not None:
        qs = qs.filter(unit_price__lte=filters.unit_price_max)
    
    # Price per night filters for lodgments
    if filters.price_per_night_min is not None:
        qs = qs.filter(lodgment__rooms__base_price_per_night__gte=filters.price_per_night_min)
    if filters.price_per_night_max is not None:
        qs = qs.filter(lodgment__rooms__base_price_per_night__lte=filters.price_per_night_max)
    
    if filters.supplier_id:
        qs = qs.filter(supplier_id=filters.supplier_id)

    # ──────────────────────────────────────────────────────────────
    # TEXT SEARCH FILTER
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
    # LOCATION FILTERS
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
    # DATE FILTERS
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
    # AVAILABILITY FILTERS
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
    
    # Available seats filters
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
    # SPECIFIC FILTERS FOR ACTIVITIES
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
    # SPECIFIC FILTERS FOR FLIGHTS
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
        # For direct flights, verify that origin and destination are different
        if filters.direct_flight:
            qs = qs.filter(
                ~Q(flights__origin_id=F('flights__destination_id'))
            )

    # ──────────────────────────────────────────────────────────────
    # SPECIFIC FILTERS FOR LODGMENTS
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
        # Calculate the difference between checkin and checkout
        from django.db.models import F
        qs = qs.filter(
            lodgment__date_checkout__gte=F('lodgment__date_checkin') + timedelta(days=filters.nights_min)
        )
    if filters.nights_max is not None:
        # Calculate the difference between checkin and checkout
        from django.db.models import F
        qs = qs.filter(
            lodgment__date_checkout__lte=F('lodgment__date_checkin') + timedelta(days=filters.nights_max)
        )
    if filters.amenities:
        for amenity in filters.amenities:
            qs = qs.filter(lodgment__amenities__contains=amenity)

    # ──────────────────────────────────────────────────────────────
    # ROOM CHARACTERISTICS FILTERS
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
    # SPECIFIC FILTERS FOR TRANSPORTATION
    # ──────────────────────────────────────────────────────────────
    if filters.transport_type:
        qs = qs.filter(transportation__type=filters.transport_type)

    # ──────────────────────────────────────────────────────────────
    # ORDERING
    # ──────────────────────────────────────────────────────────────
    if filters.ordering:
        order_map = {
            "unit_price": "unit_price",
            "-unit_price": "-unit_price",
            "date": "activity__date",
            "-date": "-activity__date",
            "name": "activity__name",
            "-name": "-activity__name",
            "rating": "unit_price",  # Placeholder - implement rating when available
            "-rating": "-unit_price",
            "popularity": "unit_price",  # Placeholder - implement popularity when available
            "-popularity": "-unit_price",
        }
        qs = qs.order_by(order_map.get(filters.ordering, "unit_price"))

    # ──────────────────────────────────────────────────────────────
    # ADVANCED FILTERS (PLACEHOLDERS)
    # ──────────────────────────────────────────────────────────────
    if filters.rating_min is not None:
        # Placeholder - implement when rating model is available
        # qs = qs.filter(average_rating__gte=filters.rating_min)
        pass
    if filters.rating_max is not None:
        # Placeholder - implement when rating model is available
        # qs = qs.filter(average_rating__lte=filters.rating_max)
        pass
    if filters.promotions_only:
        # Placeholder - implement when promotions model is available
        # qs = qs.filter(promotions__is_active=True)
        pass
    if filters.last_minute:
        # Placeholder - implement last minute offers logic
        # qs = qs.filter(is_last_minute=True)
        pass
    if filters.featured_only:
        # Placeholder - implement featured products logic
        # qs = qs.filter(is_featured=True)
        pass

    # ──────────────────────────────────────────────────────────────
    # DISTINCT TO AVOID DUPLICATES
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
    Advanced search with combined filters and more sophisticated logic
    """
    qs = ProductsMetadata.active.select_related(
        "supplier", "content_type_id"
    ).prefetch_related(
        "activity", "flight", "lodgment", "transportation",
        "activity__availabilities", "transportation__availabilities"
    )

    # Apply all filters from the main function
    qs = list_products(request, filters)
    
    # Additional logic for advanced search
    if filters.search:
        # More sophisticated search with weighting
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
    
    # Real-time availability filters
    if filters.available_only:
        today = timezone.now().date()
        qs = qs.filter(
            Q(activity__availabilities__event_date__gte=today) |
            Q(flights__available_seats__gt=0) |
            Q(transportation__availabilities__total_seats__gt=F('transportation__availabilities__reserved_seats')) |
            Q(lodgment__rooms__availabilities__available_quantity__gt=0)
        )
    
    # Order by relevance if no other ordering is specified
    if not filters.ordering:
        qs = qs.order_by('-unit_price')  # By default, order by descending price
    
    return qs


@products_router.get("/products/search/quick/", response=list[ProductsMetadataOut])
def quick_search(request, q: str, limit: int = 10):
    """
    Quick text search with result limit
    """
    qs = ProductsMetadata.active.select_related(
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


@products_router.get("/products/stats/filters/")
def get_filter_stats(request):
    """
    Gets statistics to help with filters
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


# ──────────────────────────────────────────────────────────────
# ENDPOINTS TO MANAGE FLIGHT AVAILABILITY
# ──────────────────────────────────────────────────────────────

@products_router.patch("/products/{id}/flight-availability/", response=ProductsMetadataOut)
@transaction.atomic
def update_flight_availability(request, id: int, available_seats: int):
    """
    Updates the seat availability of a flight
    """
    metadata = get_object_or_404(ProductsMetadata.active.select_related("content_type_id"), id=id)

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


@products_router.get("/products/{id}/flight-availability/")
def get_flight_availability(request, id: int):
    """
    Gets the current availability of a flight
    """
    metadata = get_object_or_404(ProductsMetadata.active.select_related("content_type_id"), id=id)

    if metadata.product_type != "flight":
        raise HttpError(400, "This product is not a flight.")

    flight = metadata.content

    return {
        "flight_id": flight.id,
        "airline": flight.airline,
        "flight_number": flight.flight_number,
        "available_seats": flight.available_seats,
        "departure_date": flight.departure_date,
        "arrival_date": flight.arrival_date,
        "is_active": flight.is_active
    }


# ──────────────────────────────────────────────────────────────
# ENDPOINTS TO MANAGE ROOM AVAILABILITY
# ──────────────────────────────────────────────────────────────

@products_router.post("/products/room-availability/", response=RoomAvailabilityOut)
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

    return {
        "id": availability.id,
        "room_id": availability.room_id,
        "start_date": availability.start_date,
        "end_date": availability.end_date,
        "available_quantity": availability.available_quantity,
        "price_override": float(availability.price_override) if availability.price_override else None,
        "currency": availability.currency,
        "is_blocked": availability.is_blocked,
        "minimum_stay": availability.minimum_stay,
        "created_at": availability.created_at,
        "updated_at": availability.updated_at
    }


@products_router.get("/products/room-availability/{id}/", response=RoomAvailabilityOut)
def get_room_availability(request, id: int):
    """
    Gets a specific room availability
    """
    availability = get_object_or_404(RoomAvailability, id=id)
    
    return {
        "id": availability.id,
        "room_id": availability.room_id,
        "start_date": availability.start_date,
        "end_date": availability.end_date,
        "available_quantity": availability.available_quantity,
        "price_override": float(availability.price_override) if availability.price_override else None,
        "currency": availability.currency,
        "is_blocked": availability.is_blocked,
        "minimum_stay": availability.minimum_stay,
        "created_at": availability.created_at,
        "updated_at": availability.updated_at
    }


@products_router.get("/products/room/{room_id}/availabilities/", response=List[RoomAvailabilityOut])
def list_room_availabilities(request, room_id: int):
    """
    Lists all availabilities of a specific room
    """
    room = get_object_or_404(Room, id=room_id, is_active=True)
    
    availabilities = room.availabilities.order_by("start_date").all()
    
    return [
        {
            "id": av.id,
            "room_id": av.room_id,
            "start_date": av.start_date,
            "end_date": av.end_date,
            "available_quantity": av.available_quantity,
            "price_override": float(av.price_override) if av.price_override else None,
            "currency": av.currency,
            "is_blocked": av.is_blocked,
            "minimum_stay": av.minimum_stay,
            "created_at": av.created_at,
            "updated_at": av.updated_at
        }
        for av in availabilities
    ]


@products_router.patch("/products/room-availability/{id}/", response=RoomAvailabilityOut)
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

    return {
        "id": availability.id,
        "room_id": availability.room_id,
        "start_date": availability.start_date,
        "end_date": availability.end_date,
        "available_quantity": availability.available_quantity,
        "price_override": float(availability.price_override) if availability.price_override else None,
        "currency": availability.currency,
        "is_blocked": availability.is_blocked,
        "minimum_stay": availability.minimum_stay,
        "created_at": availability.created_at,
        "updated_at": availability.updated_at
    }


@products_router.delete("/products/room-availability/{id}/", response={204: None})
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


@products_router.get("/products/lodgment/{lodgment_id}/rooms/availabilities/", response=List[dict])
def list_lodgment_room_availabilities(request, lodgment_id: int, start_date: date = None, end_date: date = None):
    """
    Lists all room availabilities of a lodgment
    Optionally filters by date range
    """
    lodgment = get_object_or_404(Lodgment, id=lodgment_id, is_active=True)
    
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


@products_router.get("/products/room/{room_id}/quote/", response=RoomQuoteOut)
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

@products_router.get("/products/{metadata_id}/check/", response=CheckAvailabilityOut)
def check_activity(request, metadata_id: int, qty: int, date: date, start_time: time):
    if qty <= 0:
        raise HttpError(422, "qty debe ser positivo")
    from .models import ActivityAvailability
    try:
        av = ActivityAvailability.objects.get(
            activity__product_metadata_id=metadata_id,
            event_date=date,
            start_time=start_time,
            state="active",
        )
    except ActivityAvailability.DoesNotExist:
        raise HttpError(404, "no_existe_disponibilidad")
    remaining = av.total_seats - av.reserved_seats
    enough = remaining >= qty
    status = 200 if enough else 409
    return status, CheckAvailabilityOut(
        remaining=remaining,
        enough=enough,
        unit_price=float(av.price),
        currency=av.currency,
        availability_id=av.id,
    )

@products_router.get("/products/{metadata_id}/transport/check/", response=CheckAvailabilityOut)
def check_transport(request, metadata_id: int, qty: int, date: date, time: time):
    if qty <= 0:
        raise HttpError(422, "qty debe ser positivo")
    from .models import TransportationAvailability
    try:
        av = TransportationAvailability.objects.get(
            transportation__product_metadata_id=metadata_id,
            departure_date=date,
            departure_time=time,
        )
    except TransportationAvailability.DoesNotExist:
        raise HttpError(404, "no_existe_disponibilidad")
    remaining = av.total_seats - av.reserved_seats
    enough = remaining >= qty
    status = 200 if enough else 409
    return status, CheckAvailabilityOut(
        remaining=remaining,
        enough=enough,
        unit_price=float(av.price),
        currency=av.currency,
        availability_id=av.id,
    )

@products_router.get("/products/{metadata_id}/flight/check/", response=CheckAvailabilityOut)
def check_flight(request, metadata_id: int, qty: int):
    if qty <= 0:
        raise HttpError(422, "qty debe ser positivo")
    from .models import Flights, ProductsMetadata
    try:
        flight = Flights.objects.get(product_metadata_id=metadata_id)
        meta = ProductsMetadata.objects.get(id=metadata_id)
    except Flights.DoesNotExist:
        raise HttpError(404, "no_existe_disponibilidad")
    except ProductsMetadata.DoesNotExist:
        raise HttpError(404, "no_existe_metadata")
    remaining = flight.available_seats
    enough = remaining >= qty
    status = 200 if enough else 409
    return status, CheckAvailabilityOut(
        remaining=remaining,
        enough=enough,
        unit_price=float(meta.unit_price),
        currency=meta.currency,
        availability_id=flight.id,
    )

@products_router.get("/products/room/{room_id}/check/", response=CheckAvailabilityOut)
def check_room(request, room_id: int, qty: int, start_date: date, end_date: date):
    if qty <= 0:
        raise HttpError(422, "qty debe ser positivo")
    if start_date >= end_date:
        raise HttpError(422, "start_date debe ser < end_date")
    from .models import RoomAvailability
    try:
        av = RoomAvailability.objects.get(
            room_id=room_id,
            start_date__lte=start_date,
            end_date__gte=end_date,
            is_blocked=False,
        )
    except RoomAvailability.DoesNotExist:
        raise HttpError(404, "no_existe_disponibilidad")
    remaining = av.available_quantity
    enough = remaining >= qty
    status = 200 if enough else 409
    return status, CheckAvailabilityOut(
        remaining=remaining,
        enough=enough,
        unit_price=float(av.effective_price),
        currency=av.currency,
        availability_id=av.id,
    )
