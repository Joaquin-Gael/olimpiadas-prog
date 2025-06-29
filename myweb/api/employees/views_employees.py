from typing import List, Optional

from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.responses import Response
from ninja.errors import HttpError

from api.core.auth import JWTBearer
from api.users.schemas import ErrorResponseSchema

from .models import Employees

from .schemas import (
    EmployeeCreateSchema,
    EmployeeResponseSchema,
    EmployeeUpdateSchema,
)

router = Router(tags=["Employees"])


@router.post(
    "/employees/",
    response={201: EmployeeResponseSchema, 400: ErrorResponseSchema},
    summary="Create a new employee"
)
def create_employee(request, payload: EmployeeCreateSchema):
    emp = Employees.objects.create(
        user_id=payload.user_id,
        employee_file=payload.employee_file,
        state=payload.state,
    )
    return 201, emp


@router.get(
    "/employees/",
    response=List[EmployeeResponseSchema],
    summary="List all employees"
)
def list_employees(request):
    return list(Employees.objects.all())


@router.get(
    "/employees/{employee_id}/see/",
    response={200: EmployeeResponseSchema, 404: ErrorResponseSchema},
    summary="Retrieve a single employee by ID"
)
def get_employee(request, employee_id: int):
    emp = get_object_or_404(Employees, id=employee_id)
    return emp


@router.put(
    "/employees/{employee_id}/",
    response={200: EmployeeResponseSchema, 404: ErrorResponseSchema, 400: ErrorResponseSchema},
    summary="Update an existing employee"
)
def update_employee(request, employee_id: int, payload: EmployeeUpdateSchema):
    emp = get_object_or_404(Employees, id=employee_id)
    if payload.user_id is not None:
        emp.user_id = payload.user_id
    if payload.employee_file is not None:
        emp.employee_file = payload.employee_file
    if payload.state is not None:
        emp.state = payload.state
    emp.save()
    return emp


@router.delete(
    "/employees/{employee_id}/",
    response={204: None, 404: ErrorResponseSchema},
    summary="Delete an employee"
)
def delete_employee(request, employee_id: int):
    emp = get_object_or_404(Employees, id=employee_id)
    emp.delete()
    return 204, None