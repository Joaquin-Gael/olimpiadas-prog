from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation

from api.users.models import Users


class Employees(models.Model):
    id = models.AutoField("employee_id", primary_key=True)
    user = models.OneToOneField(Users, verbose_name="user_id", on_delete=models.CASCADE)
    employee_file = models.CharField(max_length=255)
    state = models.CharField(max_length=32)
    audits = GenericRelation("Audits")

class Audits(models.Model):
    id = models.AutoField("audit_id", primary_key=True)
    employee = models.ForeignKey(Employees, verbose_name="employee_id", on_delete=models.CASCADE)
    action = models.CharField(max_length=32)
    date = models.DateTimeField(auto_now_add=True)
    observation = models.TextField()
    content_type_id = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey("content_type_id", "object_id")
