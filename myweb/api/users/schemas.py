from ninja import Schema
from typing import Optional
from datetime import date, datetime


class UserRegistrationSchema(Schema):
    """Schema para el registro de usuarios"""
    first_name: str
    last_name: str
    email: str
    telephone: str
    password: str
    born_date: Optional[date] = None
    state: str = "active" # TODO: Error de seguridad el hacer esto ya que expones un dato sensible


class UserResponseSchema(Schema):
    """Schema para la respuesta de usuarios (sin password)"""
    id: int
    first_name: str
    last_name: str
    email: str
    telephone: str
    born_date: Optional[date] = None
    state: str
    created_at: datetime
    is_staff: bool

    class Config:
        from_attributes = True


class UserUpdateSchema(Schema):
    """Schema para actualizar usuarios"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    telephone: Optional[str] = None
    born_date: Optional[date] = None
    state: Optional[str] = None


class UserLoginSchema(Schema):
    """Schema para el login de usuarios"""
    email: str
    password: str


class ErrorResponseSchema(Schema):
    """Schema para respuestas de error"""
    message: str
    detail: Optional[str] = None


class SuccessResponseSchema(Schema):
    """Schema para respuestas de éxito"""
    message: str
    data: Optional[dict] = None 