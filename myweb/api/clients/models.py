from django.db import models

from enum import Enum

from api.users.models import Users

class IdentityDocumentType(Enum):
    """
    Enumeración de los distintos tipos de formatos de documentos de identificación.
    Cada miembro representa un formato genérico de documento que puede existir en distintos países.
    ----
     Ejemplo de uso:
     >> DocumentFormat.PASSPORT.value
    'Passport'
     >> for fmt in DocumentFormat:
    ...    print(fmt.name, "=>", fmt.value)
    """
    PASSPORT = "Passport"
    NATIONAL_ID_DOCUMENT = "National Identity Document"
    ID_CARD = "Identity Card"
    RESIDENCE_PERMIT = "Residence Permit"
    DRIVER_LICENSE = "Driver's License"
    BIRTH_CERTIFICATE = "Birth Certificate"
    FOREIGNER_IDENTIFICATION_NUMBER = "Foreigner Identification Number"
    SOCIAL_SECURITY_NUMBER = "Social Security Number"
    SOCIAL_INSURANCE_NUMBER = "Social Insurance Number"
    TAX_IDENTIFICATION_NUMBER = "Tax Identification Number"
    VOTER_IDENTIFICATION_CARD = "Voter Identification Card"
    PASSPORT_CARD = "Passport Card"
    MILITARY_ID = "Military ID"
    STUDENT_ID = "Student ID"
    HEALTH_INSURANCE_CARD = "Health Insurance Card"
    VISA = "Visa"
    WORK_PERMIT = "Work Permit"
    TRAVEL_DOCUMENT = "Travel Document"
    POLICE_ID = "Police Identification Card"
    MARITIME_DOCUMENT = "Maritime Document"

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]

class Clients(models.Model):
    id = models.AutoField("client_id", primary_key=True)
    user = models.OneToOneField(Users, verbose_name="user_id", on_delete=models.CASCADE)
    identity_document_type = models.CharField(
        choices=IdentityDocumentType.choices(),
    )
    identity_document = models.CharField(max_length=255)
    state = models.CharField(max_length=32)

class AddressType(Enum):


    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]


class Addresses(models.Model):
    id = models.AutoField("address_id", primary_key=True)
    client = models.ForeignKey("Clients", verbose_name="client_id", on_delete=models.CASCADE)
    street = models.CharField(max_length=64, null=False)
    street_number = models.CharField(max_length=64, null=False)
    city = models.CharField(max_length=64, null=False)
    state = models.CharField(max_length=64, null=False)
    country = models.CharField(max_length=64, null=False)
    zip_code = models.CharField(max_length=64, null=False)
    address_type = models.CharField(choices=AddressType.choices(), null=False)
    is_default = models.BooleanField(default=False)