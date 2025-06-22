from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation

from enum import Enum

from api.clients.models import Clients

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

    def __str__(self):
        return f"*{self.__dict__}"


class Spaces(models.Model):
    id = models.AutoField("space_id", primary_key=True)
    quantity = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

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
    location = models.CharField(max_length=64)
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
        choices=DifficultyLevel.choices(),
    )
    language = models.CharField()
    space = models.ForeignKey(Spaces, verbose_name="space_id", on_delete=models.PROTECT, null=True)

    metadata = GenericRelation(
        "ProductsMetadata",
        content_type_field="content_type_id",
        object_id_field="object_id",
        related_query_name="activity",
    )

    def __str__(self):
        return f"*{self.__dict__}"


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
    destination = models.CharField(max_length=64)
    departure_date = models.DateField()
    arrival_date = models.DateField()
    duration_hours = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(192)
        ],
        help_text="duration (puede ser positivo y menor o igual a 192)"
    )
    class_flight = models.CharField(choices=ClassFlight.choices())
    space = models.ForeignKey(Spaces, verbose_name="space_id", on_delete=models.PROTECT, null=True)

    metadata = GenericRelation(
        "ProductsMetadata",
        content_type_field="content_type_id",
        object_id_field="object_id",
        related_query_name="flights",
    )

    def __str__(self):
        return f"*{self.__dict__}"

class Lodgments(models.Model):
    id = models.AutoField("lod_id", primary_key=True)
    name = models.CharField("lod_name", max_length=64)
    date_checkin = models.DateField()
    date_checkout = models.DateField()
    space = models.ForeignKey(Spaces, verbose_name="space_id", on_delete=models.PROTECT, null=True)

    metadata = GenericRelation(
        "ProductsMetadata",
        content_type_field="content_type_id",
        object_id_field="object_id",
        related_query_name="lodgment",
    )


    def __str__(self):
        return f"*{self.__dict__}"

class Transportation(models.Model):
    id = models.AutoField("transportation_id", primary_key=True)
    origin = models.CharField(max_length=64)
    destination = models.CharField(max_length=64)
    departure_date = models.DateField()
    arrival_date = models.DateField()
    description = models.TextField()
    capacity = models.IntegerField()

    metadata = GenericRelation(
        "ProductsMetadata",
        content_type_field="content_type_id",
        object_id_field="object_id",
        related_query_name="transportation",
    )

    def __str__(self):
        return f"*{self.__dict__}"

class ProductsMetadata(models.Model):
    id = models.AutoField("product_metadata_id", primary_key=True)
    supplier = models.ForeignKey(Suppliers, verbose_name="supplier_id", on_delete=models.PROTECT)
    content_type_id = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey("content_type_id", "object_id")


#TODO: Terminar de hacer los enums, a quien mrd se le ocurrio hacer tantos enums sin dar la lista

class Packages(models.Model):
    id = models.AutoField("package_id", primary_key=True)
    name = models.CharField("package_name", max_length=64)
    description = models.TextField()
    final_price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField()

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