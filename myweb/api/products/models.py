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


class ProductsMetadataManager(models.Manager):
    def with_related_data(self):
        return self.select_related('supplier', 'content_type_id').prefetch_related(
            'activity', 'flights', 'lodgment', 'transportation'
        )

class Suppliers(models.Model):
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
        help_text="House/street number (puede ser negativo hasta -2 y positivo hasta 200 000)"
    )
    city = models.CharField(max_length=64)
    country = models.CharField(max_length=64)
    email = models.EmailField()
    telephone = models.CharField(max_length=16)
    website = models.URLField()
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    active = ActiveManager()

    def __str__(self):
        return f"*{self.__dict__}"


class Location(models.Model):
    # País donde se encuentra la ubicación
    country = models.CharField(max_length=64)
    # Provincia o estado dentro del país
    state = models.CharField(max_length=64)
    # Ciudad específica
    city = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.city}, {self.state}, {self.country}"


class DifficultyLevel(Enum):
    """
    Enumeración de los niveles de dificultad para actividades.
    Cada miembro representa un grado de reto, desde muy fácil hasta extremadamente difícil.
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
    name = models.CharField(max_length=128)
    description = models.TextField()
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    date = models.DateField()
    start_time = models.TimeField()
    duration_hours = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(24)
        ],
        help_text="duration (tiene que ser positivo y menor o igual a 24)"
    )
    include_guide = models.BooleanField()
    maximum_spaces = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    difficulty_level = models.CharField(
        max_length=16,                       # ❶ añadido
        choices=DifficultyLevel.choices(),
    )
    language = models.CharField(max_length=32)
    available_slots = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        help_text="Cantidad de lugares disponibles para esta actividad"
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

    class_flight = models.CharField(max_length=32, choices=ClassFlight.choices())
    available_seats = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(500)])

    luggage_info = models.CharField(max_length=128)
    aircraft_type = models.CharField(max_length=32)
    terminal = models.CharField(max_length=16, blank=True)
    gate = models.CharField(max_length=8, blank=True)
    notes = models.TextField(blank=True)

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
    name = models.CharField(max_length=128, db_index=True)
    description = models.TextField(blank=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, db_index=True)

    # Datos clave para experiencia cliente
    type = models.CharField(
        max_length=32,
        choices=LodgmentType.choices(),
        help_text="Type of accommodation"
    )
    max_guests = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Maximum number of guests the property can accommodate"
    )

    # Información de contacto y servicios
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    amenities = models.JSONField(default=list, blank=True, help_text="List of available amenities")

    # Disponibilidad general del alojamiento
    date_checkin = models.DateField(db_index=True)
    date_checkout = models.DateField(db_index=True)

    # Timestamps y estado
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Managers
    objects = models.Manager()
    active = ActiveManager()

    # Relaciones
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
        """Verifica si el alojamiento está disponible"""
        return self.is_active and not self.deleted_at

    def get_available_rooms(self, start_date=None, end_date=None):
        """Obtiene las habitaciones disponibles para un rango de fechas"""
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

    # Capacidad y características
    capacity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Maximum number of people this room can accommodate"
    )
    has_private_bathroom = models.BooleanField(default=True)
    has_balcony = models.BooleanField(default=False)
    has_air_conditioning = models.BooleanField(default=True)
    has_wifi = models.BooleanField(default=True)

    # Precio base
    base_price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Base price per night for this room type"
    )
    currency = models.CharField(max_length=3, default="USD")

    # Estado
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
        """Verifica si la habitación está activa"""
        return self.is_active

    def get_current_availability(self, start_date, end_date):
        """Obtiene la disponibilidad actual para un rango de fechas"""
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

    # Período de disponibilidad
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)

    # Cantidad disponible y precio
    available_quantity = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of rooms of this type available for the period"
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

    # Estado y restricciones
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
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")
        if self.start_date < timezone.localdate():
            raise ValidationError("Start date cannot be in the past.")
        if self.available_quantity < 0:
            raise ValidationError("Available quantity cannot be negative.")
        if self.minimum_stay < 1:
            raise ValidationError("Minimum stay must be at least 1 night.")

    @property
    def effective_price(self):
        """Retorna el precio efectivo (override o base)"""
        return self.price_override if self.price_override else self.room.base_price_per_night

    @property
    def is_available_for_booking(self):
        """Verifica si la habitación está disponible para reserva"""
        return (
            not self.is_blocked and
            self.available_quantity > 0 and
            self.start_date >= timezone.localdate()
        )

    def get_total_price(self, nights):
        """Calcula el precio total para una cantidad de noches"""
        if nights < self.minimum_stay:
            raise ValidationError(f"Minimum stay required: {self.minimum_stay} nights")
        return self.effective_price * nights

class TransportationType(models.TextChoices):
    BUS = "bus", "Bus"
    VAN = "van", "Van"
    CAR = "car", "Auto privado"
    SHUTTLE = "shuttle", "Shuttle"
    TRAIN = "train", "Tren"
    OTHER = "other", "Otro"

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


class ProductsMetadata(models.Model):
    id = models.AutoField("product_metadata_id", primary_key=True)
    supplier = models.ForeignKey(Suppliers, on_delete=models.PROTECT)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(default=timezone.now)
    content_type_id = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey("content_type_id", "object_id")
    unit_price = models.FloatField(
        validators=[
            MinValueValidator(0)
        ],
        help_text="Precio base por unidad o persona"
    )
    product_type = models.CharField(
        choices=ProductType.choices,
        help_text="Tipo de product: actividad, vuelo, alojamiento, transporte"
    )
    is_active   = models.BooleanField(default=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    # Propiedad para obtener el tipo de producto
    @property
    def tipo_producto(self):
        model_name = self.content_type_id.model.lower()
        # Mapeo de nombres de modelos a tipos de producto en inglés
        type_mapping = {
            'activities': 'activity',
            'flights': 'flight',
            'lodgments': 'lodgment',
            'transportation': 'transportation'
        }
        return type_mapping.get(model_name, model_name)

    # Propiedad para acceder al objeto ContentType
    @property
    def content_type(self):
        return self.content_type_id

    # managers
    objects = ProductsMetadataManager()
    active = ActiveManager()

    def clean(self):
        if self.precio_unitario < 0:
            raise ValidationError("El precio no puede ser negativo")

        if not self.content:
            raise ValidationError("El producto referenciado no existe")

    def __str__(self):
        return f"{self.tipo_producto.title()} - {self.content} - ${self.precio_unitario}"

    @property
    def is_available(self):
        """Verifica si el producto está disponible"""
        return self.is_active and not self.deleted_at

    def get_final_price(self, discount_percent=0):
        """Calcula el precio final con descuento"""
        return self.precio_unitario * (1 - discount_percent / 100)


#TODO: Terminar de hacer los enums, a quien mrd se le ocurrio hacer tantos enums sin dar la lista

class Packages(models.Model):
    id = models.AutoField("package_id", primary_key=True)
    name = models.CharField("package_name", max_length=64)
    description = models.TextField()
    final_price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active  = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    active  = ActiveManager()

class ComponentPackages(models.Model):
    id = models.AutoField("component_package_id", primary_key=True)
    product_metadata = models.ForeignKey(ProductsMetadata, verbose_name="product_metadata_id", on_delete=models.CASCADE)
    package = models.ForeignKey(Packages, verbose_name="package_id", on_delete=models.PROTECT)
    order = models.IntegerField()
    quantity = models.IntegerField(null=True)

class Reviews(models.Model):
    id = models.AutoField("review_id", primary_key=True)
    product_metadata = models.ForeignKey(ProductsMetadata, verbose_name="product_metadata_id", on_delete=models.PROTECT)
    package = models.ForeignKey(Packages, verbose_name="package_id", on_delete=models.CASCADE)
    client = models.ForeignKey(Clients, verbose_name="client_id", on_delete=models.CASCADE)
    punctuation = models.FloatField()
    comment = models.TextField()
    date = models.DateField()

class Promotions(models.Model):
    id = models.AutoField("promotion_id", primary_key=True)
    product_metadata = models.ForeignKey(ProductsMetadata, verbose_name="product_metadata_id", on_delete=models.PROTECT)
    package = models.ForeignKey(Packages, verbose_name="package_id", on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    discount = models.FloatField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField()