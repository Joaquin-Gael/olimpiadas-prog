from typing import List, Optional
from datetime import datetime

from ninja import Schema
from api.users.schemas import UserResponseSchema  # adjust import to wherever your User schemas live


class AuditSchema(Schema):
    """
    Schema for the Audits model.
    """
    id: int
    action: str
    date: datetime
    observation: str
    content_type_id: int
    object_id: int


class EmployeeBaseSchema(Schema):
    """
    Shared properties for creating/updating an employee.
    """
    user_id: int
    employee_file: str
    state: str


class EmployeeCreateSchema(EmployeeBaseSchema):
    """
    Properties required to create an Employee.
    """
    pass  # all fields inherited from EmployeeBaseSchema


class EmployeeUpdateSchema(Schema):
    """
    Properties that can be updated on an Employee.
    All fields are optional to allow partial updates.
    """
    user_id: Optional[int]
    employee_file: Optional[str]
    state: Optional[str]


class EmployeeResponseSchema(EmployeeBaseSchema):
    """
    Schema returned when reading Employee data.
    Includes id, nested user info, and related audits.
    """
    id: int
    user: UserResponseSchema           # full nested user info
    audits: List[AuditSchema] = []     # list of related audits

    class Config:
        orm_mode = True
        from_attributes = True