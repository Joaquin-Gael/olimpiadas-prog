from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from api.users.models import Users


class Employees(models.Model):
    id = models.AutoField("employee_id", primary_key=True)
    user = models.OneToOneField("user_id", Users, on_delete=models.CASCADE)
    employee_file = models.CharField(max_length=255)
    state = models.CharField(max_length=32)

class Audits(models.Model):
    id = models.AutoField("audit_id", primary_key=True)
    empleado = models.ForeignKey("employee_id", Employees, on_delete=models.CASCADE)
    action = models.CharField(max_length=32)
    date = models.DateTimeField(auto_now_add=True)
    observation = models.TextField()
    content_type_id = models.ForeignKey("ContentType", on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey("content_type_id", "object_id")
