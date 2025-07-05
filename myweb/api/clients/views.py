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

from .models import Clients

from .schemas import ClientOutSchema

console = Console()

router = Router(
    tags=["Clients"],
    auth=JWTBearer()
)

@router.get(
    "/",
    response={200:List[ClientOutSchema], 404:ErrorResponseSchema},
    summary="List all clients"
)
async def list_clients(request):
    try:
        qs = await sync_to_async(Clients.objects.select_related)("user")
        clients_list: list = await sync_to_async(get_list_or_404)(qs)

        console.print(clients_list)

        serialized_list = []
        for cle in clients_list:
            serialized_list.append(
                ClientOutSchema(
                    **cle.__dict__,
                    user_first_name=cle.user.first_name,
                    user_last_name=cle.user.last_name,
                    user_email=cle.user.email
                )
            )

        console.print(serialized_list)

        return serialized_list

    except Http404 as e:
        return Response(ErrorResponseSchema(detail=str(e), message="Error al obtener la lista de clientes"), status=404)
    except Exception as e:
        raise HttpError(status_code=500, message=str(e))