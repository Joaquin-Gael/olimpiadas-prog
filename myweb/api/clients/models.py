from django.db import models

from api.users.models import Users

import uuid

class Clients(models.Model):
    id = models.UUIDField("client_id", primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(Users, on_delete=models.CASCADE)
    identity_document = models.CharField(max_length=255)