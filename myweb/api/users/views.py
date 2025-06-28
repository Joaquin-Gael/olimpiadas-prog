from django.shortcuts import render
from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.conf import settings
from ninja import Router
from ninja.responses import Response
from ninja.errors import HttpError
from typing import List
from datetime import datetime, timedelta
import jwt
from jwt import PyJWTError

from .models import Users
from .schemas import (
    UserRegistrationSchema,
    UserResponseSchema,
    UserUpdateSchema,
    UserLoginSchema,
    ErrorResponseSchema,
    SuccessResponseSchema
)

user_router = Router(tags=["users"])


@user_router.post("/register", response={201: UserResponseSchema, 400: ErrorResponseSchema})
def register_user(request, payload: UserRegistrationSchema):
    """
    Registra un nuevo usuario en el sistema
    """
    try:
        # Verificar si el email ya existe
        if Users.objects.filter(email=payload.email).exists():
            return Response(
                {"message": "El email ya está registrado", "detail": "Email duplicado"},
                status=400
            )
        
        # Verificar si el teléfono ya existe
        if Users.objects.filter(telephone=payload.telephone).exists():
            return Response(
                {"message": "El teléfono ya está registrado", "detail": "Teléfono duplicado"},
                status=400
            )
        
        # Crear el usuario
        user = Users.objects.create_user(
            email=payload.email,
            name=payload.first_name,
            last_name=payload.last_name,
            telephone=payload.telephone,
            password=payload.password,
            born_date=payload.born_date,
            state=payload.state
        )
        
        # Retornar el usuario creado (sin password)
        return Response(
            {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "telephone": user.telephone,
                "born_date": user.born_date,
                "state": user.state,
                "created_at": user.created_at,
                "is_staff": user.is_staff
            },
            status=201
        )
        
    except IntegrityError as e:
        return Response(
            {"message": "Error de integridad en la base de datos", "detail": str(e)},
            status=400
        )
    except Exception as e:
        return Response(
            {"message": "Error interno del servidor", "detail": str(e)},
            status=400
        )


@user_router.post("/login", response={200: SuccessResponseSchema, 401: ErrorResponseSchema})
def login_user(request, payload: UserLoginSchema):
    """
    Autentica un usuario y retorna información básica
    """
    try:
        # Autenticar usuario
        user = authenticate(request, email=payload.email, password=payload.password)
        
        if user is None:
            return Response(
                {"message": "Credenciales inválidas", "detail": "Email o contraseña incorrectos"},
                status=401
            )
        
        if not user.is_active:
            return Response(
                {"message": "Usuario inactivo", "detail": "El usuario está deshabilitado"},
                status=401
            )
        
        return Response(
            {
                "message": "Login exitoso",
                "data": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "is_staff": user.is_staff
                }
            },
            status=200
        )
        
    except Exception as e:
        return Response(
            {"message": "Error interno del servidor", "detail": str(e)},
            status=400
        )


@user_router.get("/", response=List[UserResponseSchema])
def list_users(request):
    """
    Lista todos los usuarios registrados
    """
    try:
        users = Users.objects.all().order_by('-created_at')
        return [
            {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "telephone": user.telephone,
                "born_date": user.born_date,
                "state": user.state,
                "created_at": user.created_at,
                "is_staff": user.is_staff
            }
            for user in users
        ]
    except Exception as e:
        raise HttpError(500, {"detail": f"Error al obtener usuarios: {str(e)}"})


@user_router.get("/{user_id}", response={200: UserResponseSchema, 404: ErrorResponseSchema})
def get_user(request, user_id: int):
    """
    Obtiene un usuario específico por ID
    """
    try:
        user = Users.objects.get(id=user_id)
        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "telephone": user.telephone,
            "born_date": user.born_date,
            "state": user.state,
            "created_at": user.created_at,
            "is_staff": user.is_staff
        }
    except Users.DoesNotExist:
        return Response(
            {"message": "Usuario no encontrado", "detail": f"No existe usuario con ID {user_id}"},
            status=404
        )
    except Exception as e:
        return Response(
            {"message": "Error interno del servidor", "detail": str(e)},
            status=400
        )


@user_router.put("/{user_id}", response={200: UserResponseSchema, 404: ErrorResponseSchema, 400: ErrorResponseSchema})
def update_user(request, user_id: int, payload: UserUpdateSchema):
    """
    Actualiza un usuario específico
    """
    try:
        user = Users.objects.get(id=user_id)
        
        # Actualizar campos si están presentes
        if payload.first_name is not None:
            user.first_name = payload.first_name
        if payload.last_name is not None:
            user.last_name = payload.last_name
        if payload.telephone is not None:
            # Verificar si el teléfono ya existe en otro usuario
            if Users.objects.filter(telephone=payload.telephone).exclude(id=user_id).exists():
                return Response(
                    {"message": "El teléfono ya está en uso", "detail": "Teléfono duplicado"},
                    status=400
                )
            user.telephone = payload.telephone
        if payload.born_date is not None:
            user.born_date = payload.born_date
        if payload.state is not None:
            user.state = payload.state
        
        user.save()
        
        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "telephone": user.telephone,
            "born_date": user.born_date,
            "state": user.state,
            "created_at": user.created_at,
            "is_staff": user.is_staff
        }
        
    except Users.DoesNotExist:
        return Response(
            {"message": "Usuario no encontrado", "detail": f"No existe usuario con ID {user_id}"},
            status=404
        )
    except IntegrityError as e:
        return Response(
            {"message": "Error de integridad en la base de datos", "detail": str(e)},
            status=400
        )
    except Exception as e:
        return Response(
            {"message": "Error interno del servidor", "detail": str(e)},
            status=400
        )


@user_router.delete("/{user_id}", response={200: SuccessResponseSchema, 404: ErrorResponseSchema})
def delete_user(request, user_id: int):
    """
    Elimina completamente un usuario de la base de datos
    """
    try:
        user = Users.objects.get(id=user_id)
        user.delete()  # Elimina completamente el usuario de la base de datos
        
        return Response(
            {"message": "Usuario eliminado exitosamente", "data": {"user_id": user_id}},
            status=200
        )
        
    except Users.DoesNotExist:
        return Response(
            {"message": "Usuario no encontrado", "detail": f"No existe usuario con ID {user_id}"},
            status=404
        )
    except Exception as e:
        return Response(
            {"message": "Error interno del servidor", "detail": str(e)},
            status=400
        )

