import pytest
from django.contrib.auth import get_user_model
from ninja.testing import TestClient
from myweb.myweb.urls import api as main_api
from api.store.models import Cart, CartItem, CartStatus
from api.products.models import ProductsMetadata, Packages
from decimal import Decimal

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass")

@pytest.fixture
def client_authed(user):
    """Cliente autenticado para tests Ninja."""
    client = TestClient(main_api)
    client._client.force_login(user)
    return client

@pytest.fixture
def package_with_metadata(db):
    package = Packages.objects.create(name="Pack Demo")
    meta = ProductsMetadata.objects.create(
        package=package,
        product_type="package",
        currency="USD",
        unit_price=Decimal("200.00"),
    )
    return meta

@pytest.fixture
def product_metadata_usd(db):
    return ProductsMetadata.objects.create(
        currency="USD",
        product_type="activity",
        unit_price=Decimal("100.00"),
    )

@pytest.fixture
def product_metadata_eur(db):
    return ProductsMetadata.objects.create(
        currency="EUR",
        product_type="activity",
        unit_price=Decimal("100.00"),
    )

@pytest.fixture
def cart_with_items(user, product_metadata_usd):
    cart = Cart.objects.create(client=user, status=CartStatus.OPEN, currency="USD")
    CartItem.objects.create(
        cart=cart,
        availability_id=1,
        product_metadata_id=product_metadata_usd.id,
        qty=1,
        unit_price=Decimal("100.00"),
        currency="USD",
        config={}
    )
    cart.items_cnt = 1
    cart.total = Decimal("100.00")
    cart.save()
    return cart 