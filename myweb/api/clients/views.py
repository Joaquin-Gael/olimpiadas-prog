from typing import List, Optional

from asgiref.sync import sync_to_async

from django.shortcuts import get_object_or_404, get_list_or_404
from django.http.response import Http404
from django.apps import apps
from django.contrib.contenttypes.models import ContentType


from ninja import Router, Query
from ninja.responses import Response
from ninja.errors import HttpError

from rich.console import Console

from api.core.auth import JWTBearer
from api.users.schemas import ErrorResponseSchema
from api.users.models import Users



console = Console()

router = Router(
    tags=["Clients"],
    auth=JWTBearer()
)