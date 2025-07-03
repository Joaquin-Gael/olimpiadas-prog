from typing import List, Optional

from asgiref.sync import sync_to_async

from django.shortcuts import get_object_or_404, get_list_or_404
from django.http.response import Http404

from ninja import Router
from ninja.responses import Response
from ninja.errors import HttpError

from rich.console import Console

from api.core.auth import JWTBearer
from api.users.schemas import ErrorResponseSchema

from .models import Sales

from .schemas import SalesOut
from ..core.auth import JWTBearer

console = Console()

router = Router(
    tags=["Sales"],
    auth=JWTBearer()
)


@router.get(
    "/",
    response={200:List[SalesOut], 404:ErrorResponseSchema},
    summary="List all sales"
)
async def list_sales(request):
    try:
        _list_sales: list = await sync_to_async(get_list_or_404)(Sales)
        serialized_sales = [SalesOut.from_orm(i) for i in _list_sales]
        return serialized_sales
    except Http404 as e:
        return Response(ErrorResponseSchema(detail=str(e), message="Error al obtener la lista de ventas"), status=404)
    except Exception as e:
        return HttpError(status_code=500, message=str(e))


@router.get(
    "/{sale_id}/",
    response={200:SalesOut, 404:ErrorResponseSchema},
    summary="Retrieve a single sale by ID"
)
async def get_sale(request, sale_id: int):
    try:
        sale = await sync_to_async(get_object_or_404)(Sales, id=sale_id)
        return SalesOut.from_orm(sale)
    except Http404 as e:
        return Response(ErrorResponseSchema(message="Error al obtener la venta", detail=str(e)), status=404)
    except Exception as e:
        console.print_exception(show_locals=True)
        return HttpError(status_code=500, message=str(e))