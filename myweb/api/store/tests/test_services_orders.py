import pytest
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from api.users.models import Users
from api.store.models import Cart, CartItem, Orders, OrderDetails
from api.products.models import Packages, ProductsMetadata, ComponentPackages
from api.store.services.services_orders import create_order_from_cart

class OrderDetailsBulkCreateTestCase(TestCase):
    def setUp(self):
        # Crear usuario
        self.user = Users.objects.create_user(email='testuser@example.com', password='1234', first_name='Test', last_name='User', telephone='123456789')
        # Crear paquete
        self.package = Packages.objects.create(name='Paquete Test', description='desc', final_price=100)
        # Crear ContentType y supplier dummy
        self.content_type = ContentType.objects.create(app_label='dummy', model='dummy')
        # NOTA: Ajusta el supplier según tu modelo real
        from api.products.models import Suppliers
        self.supplier = Suppliers.objects.create(
            first_name='Proveedor', last_name='Test', organization_name='Org', description='desc', street='Calle', street_number=1, city='Ciudad', country='Pais', email='proveedor@test.com', telephone='123', website='https://test.com'
        )
        # Crear metadata
        self.metadata = ProductsMetadata.objects.create(
            supplier=self.supplier,
            start_date=timezone.now(),
            end_date=timezone.now(),
            content_type_id=self.content_type,
            object_id=1,
            unit_price=Decimal('10.00'),
            currency='USD',
            is_active=True
        )
        # Relación ManyToMany
        ComponentPackages.objects.create(package=self.package, product_metadata=self.metadata, order=1)
        # Crear carrito y item
        self.cart = Cart.objects.create(user=self.user, status='OPEN', currency='USD', total=Decimal('10.00'), items_cnt=1)
        CartItem.objects.create(cart=self.cart, availability_id=1, product_metadata_id=self.metadata.id, qty=1, unit_price=Decimal('10.00'), currency='USD', config={})

    def test_bulk_create_orderdetails_no_attribute_error(self):
        order = create_order_from_cart(self.cart.id, self.user.id, idempotency_key='test-key')
        details = OrderDetails.objects.filter(order=order)
        self.assertEqual(details.count(), 1)
        self.assertEqual(details[0].product_metadata, self.metadata.id)
        self.assertEqual(details[0].package_id, self.package.id) 