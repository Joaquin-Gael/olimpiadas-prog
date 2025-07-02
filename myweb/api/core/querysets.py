from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.db.models import F

class ActiveQuerySet(models.QuerySet):
    def active(self):
        filters = {"deleted_at__isnull": True}
        model_fields = {f.name for f in self.model._meta.get_fields()}
        if "is_active" in model_fields:
            filters["is_active"] = True
        return self.filter(**filters)

class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = ActiveQuerySet.as_manager()

    class Meta:
        abstract = True

class ProductsMetadataQuerySet(ActiveQuerySet):
    def available_only(self):
        today = timezone.now().date()
        return (
            self.active()
            .filter(
                Q(activity__isnull=False,
                  activity__availabilities__event_date__gte=today,
                  activity__availabilities__total_seats__gt=F('activity__availabilities__reserved_seats'))
              | Q(lodgment__isnull=False,
                  lodgment__rooms__availabilities__start_date__lte=today,
                  lodgment__rooms__availabilities__end_date__gte=today,
                  lodgment__rooms__availabilities__available_quantity__gt=0)
              | Q(flights__isnull=False, flights__available_seats__gt=0)
              | Q(transportation__isnull=False, transportation__capacity__gt=0)
            )
            .distinct()
        ) 