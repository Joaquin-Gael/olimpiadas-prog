from ninja import Router

from . import views

user_router = Router(
    tags=["Users"],
)

user_router.add_router("/", views.user_public_router)
user_router.add_router("/", views.user_private_router)