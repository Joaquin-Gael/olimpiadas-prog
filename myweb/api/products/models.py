from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.utils import timezone
from .common.ActiveManager import ActiveManager
from enum import Enum
from api.clients.models import Clients
from api.core.querysets import SoftDeleteModel, ProductsMetadataQuerySet
from api.users.models import Users


class ProductsMetadataManager(models.Manager):
    def with_related_data(self):
        return self.select_related('supplier', 'content_type').prefetch_related(
            'activity', 'flights', 'lodgment', 'transportation'
        )

    def apply_filters(self, filters):
        from django.db.models import Q, F
        from datetime import timedelta
        qs = self.get_queryset().select_related(
            'supplier', 'content_type_id'
        ).prefetch_related(
            'activity', 'flight', 'lodgment', 'transportation'
        )
        # Filtros por tipo de producto
        if filters.product_type:
            if filters.product_type == "activity":
                qs = qs.filter(activity__isnull=False)
            elif filters.product_type == "flight":
                qs = qs.filter(flights__isnull=False)
            elif filters.product_type == "lodgment":
                qs = qs.filter(lodgment__isnull=False)
            elif filters.product_type == "transportation":
                qs = qs.filter(transportation__isnull=False)
        # Filtros básicos
        if filters.unit_price_min is not None:
            qs = qs.filter(unit_price__gte=filters.unit_price_min)
        if filters.unit_price_max is not None:
            qs = qs.filter(unit_price__lte=filters.unit_price_max)
        if filters.supplier_id:
            qs = qs.filter(supplier_id=filters.supplier_id)
        # Filtros de precio por noche (alojamientos)
        if filters.price_per_night_min is not None:
            qs = qs.filter(lodgment__rooms__base_price_per_night__gte=filters.price_per_night_min)
        if filters.price_per_night_max is not None:
            qs = qs.filter(lodgment__rooms__base_price_per_night__lte=filters.price_per_night_max)
        # Búsqueda de texto
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
        # Filtros de ubicación
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
        # Filtros de fechas
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
        # Filtros de disponibilidad
        if filters.available_only:
            qs = qs.available_only()
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
        # Filtros específicos por tipo
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
        if filters.airline:
            qs = qs.filter(flights__airline__icontains=filters.airline)
        if filters.class_flight:
            qs = qs.filter(flights__class_flight=filters.class_flight)
        if filters.duration_flight_min is not None:
            qs = qs.filter(flights__duration_hours__gte=filters.duration_flight_min)
        if filters.duration_flight_max is not None:
            qs = qs.filter(flights__duration_hours__lte=filters.duration_flight_max)
        if filters.direct_flight is not None:
            if filters.direct_flight:
                qs = qs.filter(~Q(flights__origin_id=F('flights__destination_id')))
        if filters.lodgment_type:
            qs = qs.filter(lodgment__type=filters.lodgment_type)
        if filters.room_type:
            qs = qs.filter(lodgment__rooms__room_type=filters.room_type)
        if filters.guests_min is not None:
            qs = qs.filter(lodgment__max_guests__gte=filters.guests_min)
        if filters.guests_max is not None:
            qs = qs.filter(lodgment__max_guests__lte=filters.guests_max)
        if filters.nights_min is not None:
            qs = qs.filter(
                lodgment__date_checkout__gte=F('lodgment__date_checkin') + timedelta(days=filters.nights_min)
            )
        if filters.nights_max is not None:
            qs = qs.filter(
                lodgment__date_checkout__lte=F('lodgment__date_checkin') + timedelta(days=filters.nights_max)
            )
        if filters.amenities:
            for amenity in filters.amenities:
                qs = qs.filter(lodgment__amenities__contains=amenity)
        # Ordenamiento
        if filters.ordering:
            qs = qs.order_by(filters.ordering)
        else:
            qs = qs.order_by('-unit_price')
        return qs

class Suppliers(SoftDeleteModel):
    id = models.AutoField("supplier_id", primary_key=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    organization_name = models.CharField(max_length=128)
    description = models.TextField()
    street = models.CharField(max_length=32)
    street_number = models.BigIntegerField(
        validators=[
            MinValueValidator(-2),
            MaxValueValidator(200_000)
        ],
        help_text="House/street number (can be negative up to -2 and positive up to 200,000)"
    )
    city = models.CharField(max_length=64)
    country = models.CharField(max_length=64)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=16)
    website = models.URLField()

    def __str__(self):
        return f"*{self.__dict__}"

    @property
    def name(self) -> str:
        """Nombre legible del proveedor para la API."""
        return self.organization_name or f"{self.first_name} {self.last_name}"


class LocationType(models.TextChoices):
    COUNTRY = "country", "Country"
    STATE = "state", "State/Province"
    CITY = "city", "City"
    DISTRICT = "district", "District/Locality"
    AIRPORT = "airport", "Airport"
    TERMINAL = "terminal", "Terminal"
    OTHER = "other", "Other"

class Location(models.Model):
    name = models.CharField(max_length=128, help_text="Display name (city, airport, etc.)", default="Non Named Location")
    country = models.CharField(max_length=64)
    state = models.CharField(max_length=64, blank=True, default="")
    city = models.CharField(max_length=64, blank=True, default="")
    code = models.CharField(max_length=16, blank=True, default="", help_text="IATA/ICAO code or custom code")
    type = models.CharField(
        max_length=16,
        choices=LocationType.choices,
        default=LocationType.CITY,
        help_text="Type of location (city, airport, terminal, etc.)"
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        help_text="Parent location (for hierarchy, e.g., city belongs to country)"
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["country", "state", "city", "type"]),
            models.Index(fields=["name"]),
            models.Index(fields=["code"]),
        ]
        ordering = ["country", "state", "city", "name"]

    def __str__(self):
        parts = [self.name]
        if self.city and self.city != self.name:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.country:
            parts.append(self.country)
        if self.code:
            parts.append(f"({self.code})")
        return ", ".join(parts)


class DifficultyLevel(Enum):
    """
    Enumeration of difficulty levels for activities.
    Each member represents a degree of challenge, from very easy to extremely difficult.
    """
    VERY_EASY = "Very Easy"
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    VERY_HARD = "Very Hard"
    EXTREME = "Extreme"

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]

class Activities(models.Model):
    id = models.AutoField("activity_id", primary_key=True)
    name = models.CharField(max_length=128, default="Non Named Activity")
    description = models.TextField()
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    date = models.DateField()
    start_time = models.TimeField()
    duration_hours = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(24)
        ],
        help_text="duration (must be positive and less than or equal to 24)"
    )
    include_guide = models.BooleanField()
    maximum_spaces = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    difficulty_level = models.CharField(
        max_length=16,
        choices=DifficultyLevel.choices(),
    )
    language = models.CharField(max_length=32)
    available_slots = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        help_text="Number of available spots for this activity"
    )
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    active = ActiveManager()
    metadata = GenericRelation(
        "ProductsMetadata",
        content_type_field="content_type_id",
        object_id_field="object_id",
        related_query_name="activity",
    )

    def __str__(self):
        return f"*{self.__dict__}"

class ActivityAvailability(models.Model):
    activity = models.ForeignKey(
        "Activities",
        on_delete=models.CASCADE,
        related_name="availabilities"
    )
    event_date = models.DateField()
    start_time = models.TimeField()
    total_seats = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Total number of seats for this activity event"
    )
    reserved_seats = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of seats already reserved"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per person for this date"
    )
    currency = models.CharField(
        max_length=8,
        help_text="Currency code (e.g., USD, ARS)"
    )
    state = models.CharField(
        max_length=32,
        default="active",
        help_text="Current availability status (e.g., active, canceled)"
    )

    def __str__(self):
        return f"{self.activity.name} - {self.event_date} @ {self.start_time}"

    def clean(self):
        if self.reserved_seats > self.total_seats:
            raise ValidationError("Reserved seats cannot exceed total seats.")
        if self.event_date < timezone.localdate():
            raise ValidationError("The event date cannot be in the past.")


class ClassFlight(Enum):
    """
    Enumeration of airline travel classes.
    Each member represents a cabin or fare class for a flight.
    """
    BASIC_ECONOMY = "Basic Economy"
    ECONOMY = "Economy"
    PREMIUM_ECONOMY = "Premium Economy"
    BUSINESS = "Business Class"
    FIRST = "First Class"

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]

class Flights(models.Model):
    id = models.AutoField("flight_id", primary_key=True)
    airline = models.CharField(max_length=32)
    flight_number = models.CharField(max_length=16)
    origin = models.ForeignKey(Location, related_name="flights_departing", on_delete=models.PROTECT)
    destination = models.ForeignKey(Location, related_name="flights_arriving", on_delete=models.PROTECT)
    departure_date = models.DateField()
    arrival_date = models.DateField()
    duration_hours = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(192)])
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    
    class_flight = models.CharField(max_length=32, choices=ClassFlight.choices())
    available_seats = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(500)])
    capacity = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(500)], help_text="Maximum number of seats for this flight")

    luggage_info = models.CharField(max_length=128)
    aircraft_type = models.CharField(max_length=32)
    terminal = models.CharField(max_length=32, null=True, blank=True)
    gate = models.CharField(max_length=32, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = GenericRelation("ProductsMetadata", content_type_field="content_type_id", object_id_field="object_id", related_query_name="flights")

    def __str__(self):
        return f"{self.airline} {self.flight_number} - {self.origin} → {self.destination}"

    def clean(self):
        if self.arrival_date < self.departure_date:
            raise ValidationError("Arrival date must be after departure date.")
        elif self.arrival_date == self.departure_date and self.arrival_time <= self.departure_time:
            raise ValidationError("When departure and arrival are on the same date, arrival time must be after departure time.")
        if self.departure_date < timezone.localdate():
            raise ValidationError("Departure date cannot be in the past.")
        if self.available_seats is not None and self.available_seats < 0:
            raise ValidationError({"available_seats": "Available seats must be greater than or equal to 0."})
        if self.duration_hours is not None and self.duration_hours < 0:
            raise ValidationError({"duration_hours": "Duration hours must be greater than or equal to 0."})


class LodgmentType(Enum):
    """
    Enumeration of lodging types.
    Each member represents a different type of accommodation.
    """
    HOTEL = "hotel"
    HOSTEL = "hostel"
    APARTMENT = "apartment"
    HOUSE = "house"
    CABIN = "cabin"
    RESORT = "resort"
    BED_AND_BREAKFAST = "bed_and_breakfast"
    VILLA = "villa"
    CAMPING = "camping"

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.replace('_', ' ').title()) for tag in cls]


class Lodgments(models.Model):
    id = models.AutoField("lodgment_id", primary_key=True)
    name = models.CharField(max_length=128, db_index=True, default="Non Named Lodgment")
    description = models.TextField(blank=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, db_index=True)

    # Key data for customer experience
    type = models.CharField(
        max_length=32,
        choices=LodgmentType.choices(),
        help_text="Type of accommodation",
        default=LodgmentType.HOTEL
    )
    max_guests = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Maximum number of guests the property can accommodate",
        default=1
    )

    # Contact and service information
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    amenities = models.JSONField(default=list, blank=True, help_text="List of available amenities")

    # General lodging availability
    date_checkin = models.DateField(db_index=True)
    date_checkout = models.DateField(db_index=True)

    # Timestamps and status
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Managers
    objects = models.Manager()
    active = ActiveManager()

    # Relations
    metadata = GenericRelation(
        "ProductsMetadata",
        content_type_field="content_type_id",
        object_id_field="object_id",
        related_query_name="lodgment",
    )

    class Meta:
        db_table = 'lodgments'
        indexes = [
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['location', 'is_active']),
            models.Index(fields=['date_checkin', 'date_checkout']),
        ]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.location})"

    def clean(self):
        if self.date_checkout <= self.date_checkin:
            raise ValidationError("Check-out date must be after check-in date.")
        if self.date_checkin < timezone.localdate():
            raise ValidationError("Check-in date cannot be in the past.")
        if self.max_guests < 1:
            raise ValidationError("Maximum guests must be at least 1.")

    @property
    def is_available(self):
        """Checks if the lodging is available"""
        return self.is_active and not self.deleted_at

    def get_available_rooms(self, start_date=None, end_date=None):
        """Gets available rooms for a date range"""
        rooms = self.rooms.filter(is_active=True)
        if start_date and end_date:
            rooms = rooms.filter(
                availabilities__start_date__lte=start_date,
                availabilities__end_date__gte=end_date,
                availabilities__available_quantity__gt=0
            )
        return rooms


class RoomType(Enum):
    """
    Enumeration of room types.
    Each member represents a different type of room configuration.
    """
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    QUADRUPLE = "quadruple"
    SUITE = "suite"
    FAMILY = "family"
    DORMITORY = "dormitory"
    STUDIO = "studio"

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]


class Room(models.Model):
    id = models.AutoField("room_id", primary_key=True)
    lodgment = models.ForeignKey(
        Lodgments,
        related_name="rooms",
        on_delete=models.CASCADE,
        db_index=True
    )
    room_type = models.CharField(
        max_length=32,
        choices=RoomType.choices(),
        db_index=True
    )
    name = models.CharField(max_length=64, blank=True, help_text="Optional room name/number")
    description = models.TextField(blank=True)

    # Capacity and characteristics
    capacity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Maximum number of people this room can accommodate"
    )
    has_private_bathroom = models.BooleanField(default=True)
    has_balcony = models.BooleanField(default=False)
    has_air_conditioning = models.BooleanField(default=True)
    has_wifi = models.BooleanField(default=True)

    # Base price
    base_price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Base price per night for this room type"
    )
    currency = models.CharField(max_length=3, default="USD")

    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rooms'
        indexes = [
            models.Index(fields=['lodgment', 'room_type']),
            models.Index(fields=['room_type', 'is_active']),
            models.Index(fields=['capacity']),
        ]
        ordering = ['lodgment', 'room_type', 'name']
        unique_together = ['lodgment', 'room_type', 'name']

    def __str__(self):
        room_name = f" - {self.name}" if self.name else ""
        return f"{self.get_room_type_display()}{room_name} - {self.lodgment.name}"

    def clean(self):
        if self.capacity < 1:
            raise ValidationError("Room capacity must be at least 1 person.")
        if self.base_price_per_night < 0:
            raise ValidationError("Base price cannot be negative.")

    @property
    def is_available(self):
        """Checks if the room is active"""
        return self.is_active

    def get_current_availability(self, start_date, end_date):
        """Gets current availability for a date range"""
        return self.availabilities.filter(
            start_date__lte=start_date,
            end_date__gte=end_date,
            available_quantity__gt=0
        ).first()


class RoomAvailability(models.Model):
    id = models.AutoField("room_availability_id", primary_key=True)
    room = models.ForeignKey(
        Room,
        related_name="availabilities",
        on_delete=models.CASCADE,
        db_index=True
    )

    # Availability period
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)

    # Available quantity and price
    available_quantity = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of rooms of this type available for the period"
    )
    max_quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Maximum number of rooms of this type for the period",
        default=1
    )
    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Override price for this period (if different from base price)"
    )
    currency = models.CharField(max_length=3, default="USD")

    # Status and restrictions
    is_blocked = models.BooleanField(
        default=False,
        help_text="If true, room is blocked and not available for booking"
    )
    minimum_stay = models.IntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text="Minimum number of nights required for booking"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'room_availabilities'
        indexes = [
            models.Index(fields=['room', 'start_date', 'end_date']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['is_blocked']),
        ]
        ordering = ['room', 'start_date']
        unique_together = ['room', 'start_date', 'end_date']

    def __str__(self):
        return f"{self.room} [{self.start_date} → {self.end_date}] - {self.available_quantity} available"

    def clean(self):
        super().clean()
        if self.end_date <= self.start_date:
            raise ValidationError({"end_date": "end_date must be after start_date"})
        if self.start_date < timezone.localdate():
            raise ValidationError({"start_date": "Start date cannot be in the past."})
        if self.available_quantity < 0:
            raise ValidationError({"available_quantity": "Available quantity cannot be negative."})
        if self.minimum_stay < 1:
            raise ValidationError({"minimum_stay": "Minimum stay must be at least 1 night."})
        # Validación de solapamiento
        overlaps = RoomAvailability.objects.filter(
            room=self.room,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        )
        if self.pk:
            overlaps = overlaps.exclude(pk=self.pk)
        if overlaps.exists():
            raise ValidationError("There is already an availability that overlaps this range.")

    @property
    def effective_price(self):
        """Returns the effective price (override or base)"""
        return self.price_override if self.price_override else self.room.base_price_per_night

    @property
    def is_available_for_booking(self):
        """Checks if the room is available for booking"""
        return (
            not self.is_blocked and
            self.available_quantity > 0 and
            self.start_date >= timezone.localdate()
        )

    def get_total_price(self, nights):
        """Calculates the total price for a number of nights"""
        if nights < self.minimum_stay:
            raise ValidationError(f"Minimum stay required: {self.minimum_stay} nights")
        return self.effective_price * nights

class TransportationType(models.TextChoices):
    BUS = "bus", "Bus"
    VAN = "van", "Van"
    CAR = "car", "Private Car"
    SHUTTLE = "shuttle", "Shuttle"
    TRAIN = "train", "Train"
    OTHER = "other", "Other"

class Transportation(models.Model):
    id = models.AutoField(primary_key=True)
    origin = models.ForeignKey("Location", related_name="transport_departures", on_delete=models.PROTECT)
    destination = models.ForeignKey("Location", related_name="transport_arrivals", on_delete=models.PROTECT)
    type = models.CharField(max_length=16, choices=TransportationType.choices, default=TransportationType.BUS)
    description = models.TextField()
    notes = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    metadata = GenericRelation(
        "ProductsMetadata",
        content_type_field="content_type_id",
        object_id_field="object_id",
        related_query_name="transportation",
    )

    def __str__(self):
        return f"{self.get_type_display().title()} – {self.origin} → {self.destination}"

    @property
    def is_available(self):
        return self.is_active and self.deleted_at is None

class TransportationAvailability(models.Model):
    transportation = models.ForeignKey(Transportation, related_name="availabilities", on_delete=models.CASCADE)
    departure_date = models.DateField()
    departure_time = models.TimeField()
    arrival_date = models.DateField()
    arrival_time = models.TimeField()
    total_seats = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    reserved_seats = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    state = models.CharField(max_length=32, default="active")  # active, canceled, etc.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["transportation", "departure_date", "departure_time"]

    def __str__(self):
        return f"{self.transportation} - {self.departure_date} @ {self.departure_time}"

    def clean(self):
        if self.reserved_seats > self.total_seats:
            raise ValidationError("Reserved seats cannot exceed total seats.")
        if self.departure_date < timezone.localdate():
            raise ValidationError("Departure date cannot be in the past.")
        if (self.arrival_date < self.departure_date) or (
            self.arrival_date == self.departure_date and self.arrival_time <= self.departure_time
        ):
            raise ValidationError("Arrival must be after departure.")


class ProductType(models.TextChoices):
    ACTIVITY       = "ACTIVITY", "Activity"
    FLIGHT         = "FLIGHT", "Flight"
    LODGMENT       = "LODGMENT", "Lodgments"
    TRANSPORTATION = "TRANSPORTATION", "Transportation"


class ProductsMetadata(SoftDeleteModel):
    id = models.AutoField("product_metadata_id", primary_key=True)
    supplier = models.ForeignKey(Suppliers, on_delete=models.PROTECT)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(default=timezone.now)
    content_type_id = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey("content_type_id", "object_id")
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Unit price of the product",
        default=0
    )
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)
    
    # Property to get the product type
    @property
    def product_type(self):
        model_name = self.content_type_id.model.lower()
        # Mapping of model names to product types in English
        type_mapping = {
            'activities': 'activity',
            'flights': 'flight',
            'lodgments': 'lodgment',
            'transportation': 'transportation'
        }
        return type_mapping.get(model_name, model_name)

    # Property to access the ContentType object
    @property
    def content_type(self):
        return self.content_type_id

    # managers
    objects = ProductsMetadataQuerySet.as_manager()

    def clean(self):
        if self.unit_price < 0:
            raise ValidationError("The price cannot be negative")

        if not self.content:
            raise ValidationError("The referenced product does not exist")

    def __str__(self):
        return f"{self.product_type.title()} - {self.content} - ${self.unit_price}"

    @property
    def is_available(self):
        """Checks if the product is available"""
        return self.is_active and not self.deleted_at

    def get_final_price(self, discount_percent=0):
        """Calculates the final price with discount"""
        return self.unit_price * (1 - discount_percent / 100)

class Category(models.Model):
    """Model to categorize tour packages"""
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active = ActiveManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']

class Packages(SoftDeleteModel):
    id = models.AutoField("package_id", primary_key=True)
    name = models.CharField("package_name", max_length=64)
    description = models.TextField()
    
    # Package category
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        help_text="Tour package category"
    )

    # Featured image to display on the web
    cover_image = models.URLField(blank=True, help_text="Featured image of the package")

    # Prices
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, 
        blank=True, 
        help_text="Base price without taxes"
    )
    taxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, 
        blank=True, 
        help_text="Taxes or surcharges"
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total final price of the package"
    )

    # Reviews (average and total)
    rating_average = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5)
        ],
        help_text="Average rating (0-5)"
    )
    total_reviews = models.IntegerField(default=0)

    # Status
    is_active = models.BooleanField(default=True)

    # Creation and update dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (${self.final_price})"

    def clean(self):
        """Validations for the Packages model"""
        if self.final_price < 0:
            raise ValidationError("The final price cannot be negative.")

        if self.base_price is not None and self.taxes is not None:
            total = round(self.base_price + self.taxes, 2)
            if round(self.final_price, 2) != total:
                raise ValidationError("The final price does not match base + taxes.")

        if self.rating_average < 0 or self.rating_average > 5:
            raise ValidationError("The average rating must be between 0 and 5.")

        if self.total_reviews < 0:
            raise ValidationError("The total number of reviews cannot be negative.")

    @property
    def duration_days(self):
        """Calculates the duration of the package based on the dates of its components"""
        start_dates = [cp.start_date for cp in self.componentpackages.all() if cp.start_date]
        end_dates = [cp.end_date for cp in self.componentpackages.all() if cp.end_date]
        if start_dates and end_dates:
            return (max(end_dates) - min(start_dates)).days + 1
        return None

class ComponentPackages(models.Model):
    id = models.AutoField("component_package_id", primary_key=True)

    package = models.ForeignKey(
        Packages, 
        verbose_name="package_id", 
        on_delete=models.PROTECT,
        related_name="componentpackages"
    )
    product_metadata = models.ForeignKey(
        ProductsMetadata, 
        verbose_name="product_metadata_id", 
        on_delete=models.CASCADE
    )

    # Extra management fields
    order = models.IntegerField(help_text="Display order within the package")
    quantity = models.IntegerField(null=True, help_text="Number of times this product is included")

    # Visual improvement and traceability
    title = models.CharField(
        max_length=128, 
        blank=True, 
        help_text="Visible name of the component in the package details"
    )

    # Specific dates for the component (optional)
    start_date = models.DateField(null=True, blank=True, help_text="Start date of component usage")
    end_date = models.DateField(null=True, blank=True, help_text="End date of component usage")

    def __str__(self):
        return f"{self.package.name} - {self.product_metadata.product_type.title()}"

    def clean(self):
        """Validations for the ComponentPackages model"""
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError("The end date cannot be earlier than the start date.")

        if self.quantity is not None and self.quantity < 1:
            raise ValidationError("The quantity must be at least 1 if specified.")

        if self.order < 0:
            raise ValidationError("The order must be greater than or equal to 0.")

    def get_summary(self):
        """Returns a summary of the component with date, type and name"""
        date_info = ""
        if self.start_date:
            date_info = f" ({self.start_date}"
            if self.end_date:
                date_info += f" - {self.end_date}"
            date_info += ")"
        
        return f"{self.product_metadata.product_type.title()}{date_info}: {self.title or self.product_metadata.content}"

class Reviews(models.Model):
    id = models.AutoField("review_id", primary_key=True)
    product_metadata = models.ForeignKey(ProductsMetadata, verbose_name="product_metadata_id", on_delete=models.PROTECT)
    package = models.ForeignKey(Packages, verbose_name="package_id", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, verbose_name="user_id", on_delete=models.CASCADE)
    punctuation = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5)
        ],
        help_text="Review rating (0-5)"
    )
    comment = models.TextField()
    date = models.DateField()

class Promotions(models.Model):
    id = models.AutoField("promotion_id", primary_key=True)
    product_metadata = models.ForeignKey(ProductsMetadata, verbose_name="product_metadata_id", on_delete=models.PROTECT)
    package = models.ForeignKey(Packages, verbose_name="package_id", on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        help_text="Discount percentage (0-100)"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField()

class StockAuditLog(models.Model):
    """
    Modelo para auditar todos los cambios en el stock de productos.
    Rastrea reservas, liberaciones, verificaciones y modificaciones.
    """
    
    class OperationType(models.TextChoices):
        RESERVE = "reserve", "Reserva"
        RELEASE = "release", "Liberación"
        CHECK = "check", "Verificación"
        MODIFY = "modify", "Modificación"
        CREATE = "create", "Creación"
        DELETE = "delete", "Eliminación"
    
    class ProductType(models.TextChoices):
        ACTIVITY = "activity", "Actividad"
        TRANSPORTATION = "transportation", "Transporte"
        ROOM = "room", "Habitación"
        FLIGHT = "flight", "Vuelo"
    
    # Información básica
    id = models.AutoField(primary_key=True)
    operation_type = models.CharField(
        max_length=16,
        choices=OperationType.choices,
        help_text="Tipo de operación realizada"
    )
    product_type = models.CharField(
        max_length=16,
        choices=ProductType.choices,
        help_text="Tipo de producto afectado"
    )
    product_id = models.IntegerField(
        help_text="ID del producto específico (availability_id, flight_id, etc.)"
    )
    
    # Detalles de la operación
    quantity = models.IntegerField(
        help_text="Cantidad involucrada en la operación"
    )
    previous_stock = models.IntegerField(
        null=True,
        blank=True,
        help_text="Stock anterior a la operación"
    )
    new_stock = models.IntegerField(
        null=True,
        blank=True,
        help_text="Stock después de la operación"
    )
    
    # Información del usuario y contexto
    user_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID del usuario que realizó la operación"
    )
    session_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="ID de sesión para rastrear operaciones"
    )
    request_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="ID único de la solicitud HTTP"
    )
    
    # Metadatos adicionales
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Información adicional en formato JSON"
    )
    success = models.BooleanField(
        default=True,
        help_text="Indica si la operación fue exitosa"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Mensaje de error si la operación falló"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stock_audit_logs'
        indexes = [
            models.Index(fields=['operation_type', 'created_at']),
            models.Index(fields=['product_type', 'product_id']),
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['success']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.operation_type} - {self.product_type} {self.product_id} - {self.created_at}"
    
    @classmethod
    def log_operation(cls, operation_type, product_type, product_id, quantity, 
                     previous_stock=None, new_stock=None, user_id=None, 
                     session_id=None, request_id=None, metadata=None, 
                     success=True, error_message=""):
        """
        Método de clase para registrar una operación de stock.
        """
        return cls.objects.create(
            operation_type=operation_type,
            product_type=product_type,
            product_id=product_id,
            quantity=quantity,
            previous_stock=previous_stock,
            new_stock=new_stock,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            metadata=metadata or {},
            success=success,
            error_message=error_message
        )


class StockChangeHistory(models.Model):
    """
    Modelo para mantener un historial detallado de cambios en el stock.
    Similar a StockAuditLog pero con más detalles sobre los cambios específicos.
    """
    
    class ChangeType(models.TextChoices):
        INCREASE = "increase", "Aumento"
        DECREASE = "decrease", "Disminución"
        SET = "set", "Establecer"
        RESET = "reset", "Reiniciar"
    
    # Información básica
    id = models.AutoField(primary_key=True)
    audit_log = models.ForeignKey(
        StockAuditLog,
        on_delete=models.CASCADE,
        related_name='changes',
        help_text="Referencia al log de auditoría principal"
    )
    change_type = models.CharField(
        max_length=16,
        choices=ChangeType.choices,
        help_text="Tipo de cambio realizado"
    )
    
    # Detalles del cambio
    field_name = models.CharField(
        max_length=32,
        help_text="Nombre del campo que cambió (reserved_seats, available_seats, etc.)"
    )
    old_value = models.IntegerField(
        null=True,
        blank=True,
        help_text="Valor anterior del campo"
    )
    new_value = models.IntegerField(
        null=True,
        blank=True,
        help_text="Nuevo valor del campo"
    )
    change_amount = models.IntegerField(
        help_text="Cantidad del cambio (positivo para aumentos, negativo para disminuciones)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stock_change_history'
        indexes = [
            models.Index(fields=['audit_log', 'field_name']),
            models.Index(fields=['change_type', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.change_type} {self.field_name}: {self.old_value} -> {self.new_value}"
    
    @classmethod
    def log_change(cls, audit_log, change_type, field_name, old_value, new_value):
        """
        Método de clase para registrar un cambio específico en el stock.
        """
        change_amount = new_value - old_value if old_value is not None and new_value is not None else 0
        
        return cls.objects.create(
            audit_log=audit_log,
            change_type=change_type,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            change_amount=change_amount
        )


class StockMetrics(models.Model):
    """
    Modelo para almacenar métricas y estadísticas de stock.
    Permite análisis y reportes de rendimiento.
    """
    
    # Información básica
    id = models.AutoField(primary_key=True)
    product_type = models.CharField(
        max_length=16,
        choices=StockAuditLog.ProductType.choices,
        help_text="Tipo de producto"
    )
    product_id = models.IntegerField(
        help_text="ID del producto específico"
    )
    
    # Métricas de stock
    total_capacity = models.IntegerField(
        help_text="Capacidad total del producto"
    )
    current_reserved = models.IntegerField(
        help_text="Cantidad actual reservada"
    )
    current_available = models.IntegerField(
        help_text="Cantidad actual disponible"
    )
    utilization_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje de utilización (0-100)"
    )
    
    # Métricas de operaciones
    total_reservations = models.IntegerField(
        default=0,
        help_text="Total de reservas realizadas"
    )
    total_releases = models.IntegerField(
        default=0,
        help_text="Total de liberaciones realizadas"
    )
    failed_operations = models.IntegerField(
        default=0,
        help_text="Total de operaciones fallidas"
    )
    
    # Fechas
    date = models.DateField(
        help_text="Fecha de las métricas"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stock_metrics'
        indexes = [
            models.Index(fields=['product_type', 'product_id', 'date']),
            models.Index(fields=['date', 'utilization_rate']),
        ]
        ordering = ['-date', '-created_at']
        unique_together = (('product_type', 'product_id', 'date'),)
    
    def __str__(self):
        return f"{self.product_type} {self.product_id} - {self.date} - {self.utilization_rate}%"
    
    @classmethod
    def update_metrics(cls, product_type, product_id, total_capacity, 
                      current_reserved, current_available, date=None):
        """
        Método de clase para actualizar las métricas de stock.
        """
        if date is None:
            date = timezone.now().date()
        
        utilization_rate = (current_reserved / total_capacity * 100) if total_capacity > 0 else 0
        
        metrics, created = cls.objects.get_or_create(
            product_type=product_type,
            product_id=product_id,
            date=date,
            defaults={
                'total_capacity': total_capacity,
                'current_reserved': current_reserved,
                'current_available': current_available,
                'utilization_rate': utilization_rate,
            }
        )
        
        if not created:
            metrics.total_capacity = total_capacity
            metrics.current_reserved = current_reserved
            metrics.current_available = current_available
            metrics.utilization_rate = utilization_rate
            metrics.save()
        
        return metrics