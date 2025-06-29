from typing import List, Optional

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, get_list_or_404

from ninja import Router
from ninja.responses import Response
from ninja.errors import HttpError, Http404

from rich.console import Console

from api.core.auth import JWTBearer
from api.users.schemas import ErrorResponseSchema
from api.users.models import Users

from .models import Employees

from .schemas import (
    EmployeeCreateSchema,
    EmployeeResponseSchema,
    EmployeeUpdateSchema,
)

console = Console()

router = Router(tags=["Employees"])


@router.post(
    "/create",
    response={201: EmployeeResponseSchema, 400: ErrorResponseSchema, 404: ErrorResponseSchema},
    summary="Create a new employee"
)
def create_employee(request, payload: EmployeeCreateSchema):
    """
    Create a new employee record.

    - Validates required fields: user_id, employee_file, state.
    - Inserts a new Employees instance into the database.
    - Returns HTTP 201 and the newly created employee on success.
    - Returns HTTP 400 with an error schema if creation fails.
    """

    try:
        _user = get_object_or_404(Users, id=payload.user_id)
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
def list_employees(request):
    """
    Retrieve a list of all employees.

    - Returns all Employees records.
    - Data is returned as a list of EmployeeResponseSchema.
    """
    try:
        _list_employees = get_list_or_404(Employees)
        serialized_list_employees = []
        for i in _list_employees:
            serialized_list_employees.append(EmployeeResponseSchema.from_orm(i))

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
def get_employee(request, employee_id: int):
    """
    Retrieve a specific employee by their ID.

    - Looks up Employees by primary key (employee_id).
    - Returns HTTP 200 and the employee data if found.
    - Returns HTTP 404 with an error schema if no employee matches.
    """
    try:
        emp = get_object_or_404(Employees, id=employee_id)
        return EmployeeResponseSchema.from_orm(emp)
    except Http404 as e:
        return Response(ErrorResponseSchema(message="Error al obtener el empleado", detail=str(e)), status=404)
    except Exception as e:
        console.print_exception(show_locals=True)
        return HttpError(status_code=500, message=str(e))


@router.put(
    "/update/{employee_id}",
    response={200: EmployeeResponseSchema, 404: ErrorResponseSchema, 400: ErrorResponseSchema},
    summary="Update an existing employee"
)
def update_employee(request, employee_id: int, payload: EmployeeUpdateSchema):
    """
    Update an existing employee's information.

    - Fields user_id, employee_file, and state are optional in the payload.
    - Only provided fields are updated on the Employees record.
    - Returns HTTP 200 and the updated employee on success.
    - Returns HTTP 404 if the employee does not exist.
    - Returns HTTP 400 if any validation or update error occurs.
    """
    try:
        emp = get_object_or_404(Employees, id=employee_id)
        if payload.user_id is not None:
            emp.user_id = payload.user_id
        if payload.employee_file is not None:
            emp.employee_file = payload.employee_file
        if payload.state is not None:
            emp.state = payload.state
        emp.save()
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
    response={200: None, 404: ErrorResponseSchema},
    summary="Delete an employee"
)
def delete_employee(request, employee_id: int):
    """
    Delete an employee record by their ID.

    - Removes the Employees instance from the database.
    - Returns HTTP 204 on successful deletion with no content.
    - Returns HTTP 404 with an error schema if the employee does not exist.
    """
    try:
        emp = get_object_or_404(Employees, id=employee_id)
        emp.delete()
        return None
    except Http404 as e:
        return Response(ErrorResponseSchema(message="Error al obtener el empleado para eliminación", detail=str(e)), status_code=404)
    except Exception as e:
        console.print_exception(show_locals=True)
        return HttpError(status_code=500, message=str(e))