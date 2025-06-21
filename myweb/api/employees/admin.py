from django.contrib import admin

from .models import Employees, Audits


@admin.register(Employees)
class EmployeesAdmin(admin.ModelAdmin):
    pass


@admin.register(Audits)
class AuditsAdmin(admin.ModelAdmin):
    pass