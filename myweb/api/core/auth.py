import jwt
from asgiref.sync import sync_to_async
from jwt import PyJWTError

from datetime import datetime, timedelta

from ninja.errors import HttpError
from ninja.security import HttpBearer

from typing import Optional, List, Tuple, Union

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
        payload.setdefault("exp", int((datetime.now() + settings.JWT_REFRESH_TOKEN_EXPIRES).timestamp()))
        payload.setdefault("type", "refresh_token")
    else:
        payload.setdefault("exp", int((datetime.now() + settings.JWT_TOKEN_EXPIRES).timestamp()))
    return jwt.encode(payload, key=settings.SECRET_KEY, algorithm=settings.JWT_HASH_ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, key=settings.SECRET_KEY, algorithms=[settings.JWT_HASH_ALGORITHM], leeway=20)
        return payload
    except PyJWTError as e:
        console.print("JWT Decode Error: ", e)
        raise ValueError("Value Not Found") from e

class JWTBearer(HttpBearer):
    def __init__(self, permissions: Optional[Union[List[str],Tuple[str]]] = None):
        super().__init__()
        self.permissions = permissions if not permissions is None else []

    async def authenticate(self, request: HttpRequest, token: str) -> Users:
        console.rule("Token")
        console.print(token)
        console.rule("Token arriba")
        if not token.startswith("Bearer "):
            raise HttpError(status_code=403, message="Invalid token format")

        token = token.split(" ")[1]

        try:
            payload = decode_token(token)
        except ValueError as e:
            raise HttpError(status_code=401, message="Invalid token: " + str(e))

        scopes = payload.get("scopes", [])

        if not all(perm in scopes for perm in self.permissions):
            console.print(f"Permisos: {self.permissions}")
            console.print(f"Scopes: {scopes}")
            raise HttpError(status_code=403, message="Missing permissions")

        current_route = request.resolver_match.route

        if current_route != f"{settings.ID_PREFIX}/users/refresh" and payload.get("type") == "refresh_token":
            raise HttpError(status_code=401, message="Refresh token used in non-refresh endpoint")

        if current_route == f"{settings.ID_PREFIX}/users/refresh" and payload.get("type") != "refresh_token":
            raise HttpError(status_code=401, message="Access token used in refresh endpoint")

        user_id = payload.get("sub")

        if not user_id:
            raise HttpError(status_code=401, message="Missing user ID in token")

        try:

            user = await sync_to_async(get_object_or_404)(Users, id=user_id)

            request.user = user
            request.scopes = scopes
            return user

        except Http404:
            raise HttpError(404, f"Usuario con ID {user_id} no encontrado")

        except Exception as e:
            console.print(e)
            raise HttpError(status_code=401, message="Invalid or expired token")