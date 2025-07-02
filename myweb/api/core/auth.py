import jwt
from asgiref.sync import sync_to_async
from jwt import PyJWTError

from datetime import datetime, timedelta

from ninja.errors import HttpError
from ninja.security import HttpBearer
from ninja import Header

from typing import Optional

from django.conf import settings
from django.http import HttpRequest, Http404
from django.shortcuts import get_object_or_404

from rich.console import Console

from api.users.models import Users

console = Console()

def gen_token(payload: dict, refresh: bool = False) -> str:
    payload.setdefault("iat", datetime.now())
    payload.setdefault("iss", f"{settings.API_TITLE}/{settings.API_VERSION}")
    if refresh:
        payload.setdefault("exp", int((datetime.now() + timedelta(minutes=30)).timestamp()))
        payload.setdefault("type", "refresh_token")
    else:
        payload.setdefault("exp", int((datetime.now() + timedelta(minutes=15)).timestamp()))
    return jwt.encode(payload, key=settings.SECRET_KEY, algorithm=settings.JWT_HASH_ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, key=settings.SECRET_KEY, algorithms=[settings.JWT_HASH_ALGORITHM], leeway=20)
        return payload
    except PyJWTError as e:
        console.print("JWT Decode Error: ", e)
        raise ValueError("Value Not Found") from e

class JWTBearer(HttpBearer):
    async def authenticate(self, request: HttpRequest, token: str) -> Users:
        console.rule("Token")
        console.print(token)
        console.rule("Token arriba")
        if not token.startswith("Bearer "):
            raise HttpError(status_code=403, message="Invalid token format")

        token = token.split(" ")[1]

        try:
            payload = decode_token(token)
            print("DEBUG JWT PAYLOAD:", payload)  # Debug
        except ValueError as e:
            raise HttpError(status_code=401, message="Invalid token: " + str(e))

        current_route = request.resolver_match.route

        if current_route != "/refresh-token" and payload.get("type") == "refresh_token":
            raise HttpError(status_code=401, message="Refresh token used in non-refresh endpoint")

        user_id = payload.get("sub")
        print("DEBUG JWT USER_ID:", user_id)  # Debug

        if not user_id:
            raise HttpError(status_code=401, message="Missing user ID in token")

        # Buscar usuario
        try:
<<<<<<< HEAD

            user = await sync_to_async(get_object_or_404)(Users, id=user_id)

=======
            user = get_object_or_404(Users, id=user_id)
>>>>>>> 1e5be1dd49007289eb0670dce677d47358a2b9e9
            request.user = user
            request.scopes = payload.get("scopes", [])
            return user
        except Http404:
            print("DEBUG JWT USER NOT FOUND")  # Debug
            raise HttpError(404, f"Usuario con ID {user_id} no encontrado")
        except Exception as e:
            print(e)
            raise HttpError(status_code=401, message="Invalid or expired token")