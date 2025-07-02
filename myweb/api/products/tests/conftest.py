import pytest
from django.contrib.auth import get_user_model
from api.products.models import Suppliers, Location
from datetime import date
from ninja.testing import TestClient
from ninja import NinjaAPI, Router
import uuid

@pytest.fixture
def ninja_client():
    """Ninja client for testing with all routers"""
    # Create a new API instance for each test with unique namespace
    unique_id = str(uuid.uuid4())[:8]
    api = NinjaAPI(urls_namespace=f"test-{unique_id}")
    
    # Import router functions to recreate them
    from api.products.views_products import (
        create_product, create_complete_activity, create_complete_lodgment, 
        create_complete_transport, get_product, update_product, deactivate_product
    )
    
    from api.products.views_package import (
        list_packages, get_package, create_package, update_package, delete_package,
        list_package_components, add_package_component, update_package_component,
        remove_package_component, get_featured_packages, get_packages_by_price_range,
        get_packages_by_duration, get_packages_stats, list_categories, get_category,
        create_category, update_category, delete_category, get_packages_by_category
    )
    
    # Create unique routers for each test
    products_router = Router(tags=["Products"])
    package_router = Router(tags=["Packages"])
    category_router = Router(tags=["Categories"])
    
    # Add only the endpoints needed for package tests
    products_router.add_api_operation("/create/", ["POST"], create_product)
    products_router.add_api_operation("/activity-complete/", ["POST"], create_complete_activity)
    products_router.add_api_operation("/lodgment-complete/", ["POST"], create_complete_lodgment)
    products_router.add_api_operation("/transport-complete/", ["POST"], create_complete_transport)
    products_router.add_api_operation("/{id}/", ["GET"], get_product)
    products_router.add_api_operation("/{id}/", ["PATCH"], update_product)
    products_router.add_api_operation("/{id}/", ["DELETE"], deactivate_product)
    
    # Add package endpoints
    package_router.add_api_operation("/", ["GET"], list_packages)
    package_router.add_api_operation("/{package_id}", ["GET"], get_package)
    package_router.add_api_operation("/", ["POST"], create_package)
    package_router.add_api_operation("/{package_id}", ["PUT"], update_package)
    package_router.add_api_operation("/{package_id}", ["DELETE"], delete_package)
    package_router.add_api_operation("/{package_id}/components", ["GET"], list_package_components)
    package_router.add_api_operation("/{package_id}/components", ["POST"], add_package_component)
    package_router.add_api_operation("/{package_id}/components/{component_id}", ["PUT"], update_package_component)
    package_router.add_api_operation("/{package_id}/components/{component_id}", ["DELETE"], remove_package_component)
    package_router.add_api_operation("/search/featured", ["GET"], get_featured_packages)
    package_router.add_api_operation("/search/by-price-range", ["GET"], get_packages_by_price_range)
    package_router.add_api_operation("/search/by-duration", ["GET"], get_packages_by_duration)
    package_router.add_api_operation("/stats/overview", ["GET"], get_packages_stats)
    
    # Add category endpoints
    category_router.add_api_operation("/", ["GET"], list_categories)
    category_router.add_api_operation("/{category_id}", ["GET"], get_category)
    category_router.add_api_operation("/", ["POST"], create_category)
    category_router.add_api_operation("/{category_id}", ["PUT"], update_category)
    category_router.add_api_operation("/{category_id}", ["DELETE"], delete_category)
    category_router.add_api_operation("/{category_id}/packages", ["GET"], get_packages_by_category)
    
    api.add_router("/products/", products_router)
    api.add_router("/package/", package_router)
    api.add_router("/categories/", category_router)
    
    return TestClient(api)

@pytest.fixture
def supplier():
    """Create a test supplier"""
    return Suppliers.objects.create(
        first_name="John",
        last_name="Smith",
        organization_name="Adventure Tours",
        description="Adventure tourism company",
        street="Main St",
        street_number=123,
        city="Bariloche",
        country="Argentina",
        email="john@adventuretours.com",
        telephone="+54 294 1234567",
        website="https://adventuretours.com"
    )

@pytest.fixture
def location():
    """Create a test location"""
    return Location.objects.create(
        country="Argentina",
        state="Río Negro",
        city="Bariloche"
    ) 

import pytest
from datetime import date, timedelta
from api.products.models import Activities, Flights, Lodgment, Transportation, ProductsMetadata
from django.contrib.contenttypes.models import ContentType

@pytest.fixture
def lodgment_metadata(supplier, location):
    lodgment = Lodgment.objects.create(
        name="Test Hotel",
        description="Description",
        location=location,
        type="hotel",
        max_guests=2,
        contact_phone="123",
        contact_email="test@hotel.com",
        amenities=[],
        date_checkin=date.today(),
        date_checkout=date.today() + timedelta(days=2),
    )
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=ContentType.objects.get_for_model(Lodgment),
        object_id=lodgment.id,
        unit_price=1000,
    )
    return metadata

@pytest.fixture
def activity_metadata(supplier, location):
    activity = Activities.objects.create(
        name="Test Activity",
        description="Description",
        location=location,
        date=date.today() + timedelta(days=1),
        start_time="10:00:00",
        duration_hours=2,
        include_guide=True,
        maximum_spaces=10,
        difficulty_level="Easy",
        language="en",
        available_slots=10,
    )
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=ContentType.objects.get_for_model(Activities),
        object_id=activity.id,
        unit_price=200,
    )
    return metadata

@pytest.fixture
def flight_metadata(supplier, location):
    flight = Flights.objects.create(
        airline="TestAir",
        flight_number="TA123",
        origin=location,
        destination=location,
        departure_date=date.today() + timedelta(days=1),
        departure_time="12:00:00",
        arrival_date=date.today() + timedelta(days=1),
        arrival_time="14:00:00",
        duration_hours=2,
        class_flight="Economy",
        available_seats=100,
        luggage_info="1 suitcase",
        aircraft_type="Boeing 737",
    )
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=ContentType.objects.get_for_model(Flights),
        object_id=flight.id,
        unit_price=500,
    )
    return metadata

@pytest.fixture
def transportation_metadata(supplier, location):
    transport = Transportation.objects.create(
        origin=location,
        destination=location,
        type="bus",
        description="Test transportation",
        notes="",
        capacity=40,
    )
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_type_id=ContentType.objects.get_for_model(Transportation),
        object_id=transport.id,
        unit_price=300,
    )
    return metadata