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

from .models import Employees

from .schemas import (
    EmployeeCreateSchema,
    EmployeeResponseSchema,
    EmployeeUpdateSchema,
    EmployeeDeleteSchema,
    AuditSchema,
    EmployeeAuditsScheme
)

console = Console()

router = Router(
    tags=["Employees"],
    auth=JWTBearer()
)


@router.post(
    "/create",
    response={201: EmployeeResponseSchema, 400: ErrorResponseSchema, 404: ErrorResponseSchema},
    summary="Create a new employee"
)
async def create_employee(request, payload: EmployeeCreateSchema):
    """
    Create a new employee record.

    - Validates required fields: user_id, employee_file, state.
    - Inserts a new Employees instance into the database.
    - Returns HTTP 201 and the newly created employee on success.
    - Returns HTTP 400 with an error schema if creation fails.
    """

    try:
        _user = await sync_to_async(get_object_or_404)(Users, id=payload.user_id)
        emp = Employees.objects.create(
            user=_user,
            employee_file=payload.employee_file,
        )
        return EmployeeResponseSchema.from_orm(emp)
    except Http404 as e:
        return Response(ErrorResponseSchema(message="Error al obtener el usuario referenciado", detail=str(e)), status=404)
    except Exception as e:
        console.print_exception(show_locals=True)
        return HttpError(status_code=500, message=str(e))


@router.get(
    "/",
    response={200:List[EmployeeResponseSchema], 404:ErrorResponseSchema},
    summary="List all employees"
)
async def list_employees(request):
    """
    Retrieve a list of all employees.

    - Returns all Employees records.
    - Data is returned as a list of EmployeeResponseSchema.
    """
    try:
        _list_employees = await sync_to_async(get_list_or_404)(Employees)
        serialized_list_employees = [EmployeeResponseSchema.from_orm(i) for i in _list_employees]

        return serialized_list_employees
    except Http404 as e:
        return Response(ErrorResponseSchema(detail=str(e), message="Error al obtener la lista de empleados"), status=404)
    except Exception as e:
        return HttpError(status_code=500, message=str(e))

@router.get(
    "/{employee_id}/see",
    response={200: EmployeeResponseSchema, 404: ErrorResponseSchema},
    summary="Retrieve a single employee by ID"
)
async def get_employee(request, employee_id: int):
    """
    Retrieve a specific employee by their ID.

    - Looks up Employees by primary key (employee_id).
    - Returns HTTP 200 and the employee data if found.
    - Returns HTTP 404 with an error schema if no employee matches.
    """
    try:
        emp = await sync_to_async(get_object_or_404)(Employees, id=employee_id)
        return EmployeeResponseSchema.from_orm(emp)
    except Http404 as e:
        return Response(ErrorResponseSchema(message="Error al obtener el empleado", detail=str(e)), status=404)
    except Exception as e:
        console.print_exception(show_locals=True)
        return HttpError(status_code=500, message=str(e))

@router.get(
    "/{employee_id}/audits",
    response={200: List[AuditSchema], 404: ErrorResponseSchema, 400: ErrorResponseSchema},
    summary="Retrieve employee audits"
)
async def get_employee_audits(request, employee_id: int, start: Optional[int] = 0, limit: Optional[int] = 10):
    try:
        emp = await sync_to_async(get_object_or_404)(Employees, id=employee_id)

        audits = emp.audits.all().order_by('-date')[start:limit]
        serialized_audits = [AuditSchema.from_orm(i) for i in audits]

        return serialized_audits

    except Http404 as e:
        return Response(ErrorResponseSchema(message="Error al obtener el empleado", detail=str(e)), status=404)
    except Exception as e:
        console.print_exception(show_locals=True)
        return HttpError(status_code=500, message=str(e))


@router.get(
    "/{employee_id}/audits"
)
async def get_employee_audits_paginated(request, employee_id: int, query: EmployeeAuditsScheme = Query(...)):
    try:
        emp = get_object_or_404(Employees, id=employee_id)

        _model = apps.get_model('products', query.product_type)

        ct = ContentType.objects.get_for_model(_model)

        audits: list = emp.audits.filter(action=query.action, content_type=ct).order_by('-date')

        serialized_audist = [AuditSchema.from_orm(i) for i in audits]

        return serialized_audist

    except Exception as e:
        return HttpError(status_code=500, message=str(e))

@router.put(
    "/update/{employee_id}",
    response={200: EmployeeResponseSchema, 404: ErrorResponseSchema, 400: ErrorResponseSchema},
    summary="Update an existing employee"
)
async def update_employee(request, employee_id: int, payload: EmployeeUpdateSchema):
    """
    Update an existing employee's information.

    - Fields user_id, employee_file, and state are optional in the payload.
    - Only provided fields are updated on the Employees record.
    - Returns HTTP 200 and the updated employee on success.
    - Returns HTTP 404 if the employee does not exist.
    - Returns HTTP 400 if any validation or update error occurs.
    """
    try:
        emp = await sync_to_async(get_object_or_404)(Employees, id=employee_id)
        if payload.user_id is not None:
            emp.user_id = payload.user_id
        if payload.employee_file is not None:
            emp.employee_file = payload.employee_file
        if payload.state is not None:
            emp.state = payload.state
        await sync_to_async(emp.save)()
        return EmployeeResponseSchema.from_orm(emp)
    except Http404 as e:
        return Response(
            ErrorResponseSchema(message="Error al obtener el empleado", detail=str(e)), status=404,
        )
    except Exception as e:
        console.print_exception(show_locals=True)
        return HttpError(status_code=500, message=str(e))


@router.delete(
    "/delete/{employee_id}",
    response={204: EmployeeDeleteSchema, 404: ErrorResponseSchema},
    summary="Delete an employee"
)
async def delete_employee(request, employee_id: int):
    """
    Delete an employee record by their ID.

    - Removes the Employees instance from the database.
    - Returns HTTP 204 on successful deletion with EmployeeDeleteSchema content.
    - Returns HTTP 404 with an error schema if the employee does not exist.
    """
    try:
        emp = await sync_to_async(get_object_or_404)(Employees, id=employee_id)
        await sync_to_async(emp.delete)()
        return EmployeeDeleteSchema(
            message="Employee {} deleted".format(employee_id),
            id=emp.id
        )
    except Http404 as e:
        return Response(ErrorResponseSchema(message="Error al obtener el empleado para eliminación", detail=str(e)), status_code=404)
    except Exception as e:
        console.print_exception(show_locals=True)
        return HttpError(status_code=500, message=str(e))