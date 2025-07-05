from ninja import Schema
from typing import List, Optional, Literal
from datetime import date, datetime
from pydantic import EmailStr, Field
from api.users.schemas import UserResponseSchema

from api.products.schemas import BaseSchema

# ── Schemas para Clients ────────────────────────────────────────
#class ClientCreateSchema(Schema):
#    """Schema para crear un cliente"""
#    user_id: int = Field(..., description="ID del usuario asociado")
#    identity_document_type: str = Field(..., description="Tipo de documento de identidad")
#    identity_document: str = Field(..., description="Número del documento de identidad")
#    state: str = Field(default="active", description="Estado del cliente")
#
#class ClientUpdateSchema(Schema):
#    """Schema para actualizar un cliente"""
#    identity_document_type: Optional[str] = Field(None, description="Tipo de documento de identidad")
#    identity_document: Optional[str] = Field(None, description="Número del documento de identidad")
#    state: Optional[str] = Field(None, description="Estado del cliente")
#
#class ClientResponseSchema(Schema):
#    """Schema de respuesta para clientes"""
#    id: int
#    user_id: int
#    identity_document_type: str
#    identity_document: str
#    state: str
#    user: UserResponseSchema  # Información completa del usuario
#
#    class Config:
#        from_attributes = True
#
class ClientOutSchema(BaseSchema):
    """Schema para listar clientes (sin información detallada del usuario)"""
    id: int
    user_id: int
    identity_document_type: str
    identity_document: str
    state: str
    user_first_name: str
    user_last_name: str
    user_email: str

## ── Schemas para Addresses ──────────────────────────────────────
#class AddressCreateSchema(Schema):
#    """Schema para crear una dirección"""
#    client_id: int = Field(..., description="ID del cliente")
#    street: str = Field(..., max_length=64, description="Nombre de la calle")
#    street_number: str = Field(..., max_length=64, description="Número de la calle")
#    city: str = Field(..., max_length=64, description="Ciudad")
#    state: str = Field(..., max_length=64, description="Estado/Provincia")
#    country: str = Field(..., max_length=64, description="País")
#    zip_code: str = Field(..., max_length=64, description="Código postal")
#    address_type: str = Field(..., description="Tipo de dirección (Home, Work, Billing, etc.)")
#    is_default: bool = Field(default=False, description="Si es la dirección por defecto")
#
#class AddressUpdateSchema(Schema):
#    """Schema para actualizar una dirección"""
#    street: Optional[str] = Field(None, max_length=64)
#    street_number: Optional[str] = Field(None, max_length=64)
#    city: Optional[str] = Field(None, max_length=64)
#    state: Optional[str] = Field(None, max_length=64)
#    country: Optional[str] = Field(None, max_length=64)
#    zip_code: Optional[str] = Field(None, max_length=64)
#    address_type: Optional[str] = Field(None, description="Tipo de dirección")
#    is_default: Optional[bool] = Field(None, description="Si es la dirección por defecto")
#
#class AddressResponseSchema(Schema):
#    """Schema de respuesta para direcciones"""
#    id: int
#    client_id: int
#    street: str
#    street_number: str
#    city: str
#    state: str
#    country: str
#    zip_code: str
#    address_type: str
#    is_default: bool
#
#    class Config:
#        from_attributes = True
#
## ── Schemas para Client con Addresses ───────────────────────────
#class ClientWithAddressesSchema(ClientResponseSchema):
#    """Schema de respuesta para clientes con sus direcciones"""
#    addresses: List[AddressResponseSchema] = []
#
## ── Schemas para Filtros ────────────────────────────────────────
#class ClientFilterSchema(Schema):
#    """Schema para filtrar clientes"""
#    state: Optional[str] = Field(None, description="Filtrar por estado")
#    identity_document_type: Optional[str] = Field(None, description="Filtrar por tipo de documento")
#    search: Optional[str] = Field(None, description="Buscar por nombre, email o documento")
#    limit: int = Field(10, ge=1, le=100, description="Límite de resultados")
#
#class AddressFilterSchema(Schema):
#    """Schema para filtrar direcciones"""
#    client_id: Optional[int] = Field(None, description="Filtrar por cliente")
#    address_type: Optional[str] = Field(None, description="Filtrar por tipo de dirección")
#    country: Optional[str] = Field(None, description="Filtrar por país")
#    is_default: Optional[bool] = Field(None, description="Filtrar por dirección por defecto")
#
## ── Schemas para Respuestas ─────────────────────────────────────
#class ClientSuccessResponse(Schema):
#    """Schema para respuestas exitosas de clientes"""
#    message: str
#    client: ClientResponseSchema
#
#class AddressSuccessResponse(Schema):
#    """Schema para respuestas exitosas de direcciones"""
#    message: str
#    address: AddressResponseSchema
#
#class ClientErrorResponse(Schema):
#    """Schema para respuestas de error de clientes"""
#    message: str
#    error_code: Optional[str] = None
#    details: Optional[dict] = None
#