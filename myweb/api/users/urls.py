from ninja import Router

from .models import Users

user_router = Router(
    tags=["users"],
)