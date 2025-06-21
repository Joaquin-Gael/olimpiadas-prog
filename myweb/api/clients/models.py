from django.db import models

from enum import Enum

from api.users.models import Users

class IdentityDocumentType(Enum):

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]

class Clients(models.Model):
    id = models.AutoField("client_id", primary_key=True)
    user = models.OneToOneField("user_id", Users, on_delete=models.CASCADE)
    identity_document_type = models.CharField(
        choices=IdentityDocumentType.choices(),
    )
    identity_document = models.CharField(max_length=255)
    state = models.CharField(max_length=32)

class AddressType(Enum):


    @classmethod
    def choices(cls):
        return [(tag.value, tags.name.title()) for tag in cls]


class Addresses(models.Model):
    id = models.AutoField("address_id", primary_key=True)
    client = models.ForeignKey("Clients", on_delete=models.CASCADE)
    street = models.CharField(max_length=64, null=False)
    street_number = models.CharField(max_length=64, null=False)
    city = models.CharField(max_length=64, null=False)
    state = models.CharField(max_length=64, null=False)
    country = models.CharField(max_length=64, null=False)
    zip_code = models.CharField(max_length=64, null=False)
    address_type = models.CharField(choices=AddressType.choices(), null=False)
    is_default = models.BooleanField(default=False)