from django.contrib import admin

from .models import Clients

@admin.register(Clients)
class ClientsAdmin(admin.ModelAdmin):
    pass
