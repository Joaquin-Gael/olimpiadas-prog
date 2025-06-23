from ninja import Router

from .models import Users
from . import views

user_router = Router(
    tags=["users"],
)

# Incluir todas las rutas de usuarios
user_router.add_router("/", views.user_router)