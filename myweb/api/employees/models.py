from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation

from enum import Enum

from api.users.models import Users


class Employees(models.Model):
    id = models.AutoField("employee_id", primary_key=True)
    user = models.OneToOneField(Users, verbose_name="user_id", on_delete=models.CASCADE)
    employee_file = models.CharField(max_length=255)
    state = models.CharField(max_length=32)
    audits = GenericRelation("Audits")

class AuditAction(Enum):
    CREATE = 'Create'
    READ = 'Read'
    UPDATE = 'Update'
    DELETE = 'Delete'

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]

class Audits(models.Model):
    id = models.AutoField("audit_id", primary_key=True)
    employee = models.ForeignKey(Employees, verbose_name="employee_id", on_delete=models.CASCADE)
    action = models.CharField(max_length=32, choices=AuditAction.choices(), default=AuditAction.READ.value)
    date = models.DateTimeField(auto_now_add=True)
    observation = models.TextField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey("content_type_id", "object_id")

    class Meta:
        indexes = [
            models.Index(fields=['content_type_id', 'object_id']),
        ]