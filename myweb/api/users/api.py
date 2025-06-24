from django.shortcuts import render
from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.conf import settings
from django.http import HttpResponse
import json, jwt
from .utils import *
from ninja import Router
from ninja.responses import Response
from ninja.errors import HttpError
from typing import List
from datetime import datetime, timedelta
from jwt import PyJWTError

from .models import Users
from .schemas import *

user_router = Router(tags=["users"])

from ninja import Schema



@user_router.post("/refresh")
def refresh_token(request, payload: RefreshTokenSchema):
    """
    Genera un nuevo access token usando un refresh token válido.
    """
    try:
        # Decodificar el refresh token
        refresh_payload = jwt.decode(payload.refresh_token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        
        # Verificar que es un refresh token
        if refresh_payload.get('type') != 'refresh':
            return Response({"message": "Token inválido, no es un refresh token"}, status=401)
        
        user_id = refresh_payload.get('user_id')
        if not user_id:
            return Response({"message": "El token no contiene user_id"}, status=401)
        
        # Verificar que el usuario existe
        user = User.objects.get(id=user_id)
        if not user.is_active:
            return Response({"message": "Usuario inactivo"}, status=401)
        
        # Generar un nuevo access token
        access_payload = {
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRATION),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        new_access_token = jwt.encode(access_payload, settings.JWT_SECRET_KEY, algorithm='HS256')
        
        return Response({
            "message": "Token renovado",
            "access_token": new_access_token
        }, status=200)
    
    except jwt.ExpiredSignatureError:
        return Response({"message": "Refresh token expirado"}, status=401)
    except jwt.InvalidTokenError:
        return Response({"message": "Refresh token inválido"}, status=401)
    except User.DoesNotExist:
        return Response({"message": "Usuario no encontrado"}, status=401)

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


@user_router.post("/login")
def login_user(request, payload: UserLoginSchema):
    """
    Autentica al usuario y devuelve un access token y un refresh token.
    """
    user = authenticate(request, email=payload.email, password=payload.password)
    
    if user is None or not user.is_active:
        return Response(
            {"message": "Credenciales inválidas o usuario inactivo"},
            status=401
        )
    
    # Generar access token
    access_payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRATION),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    access_token = jwt.encode(access_payload, settings.JWT_SECRET_KEY, algorithm='HS256')
    
    # Generar refresh token
    refresh_payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(seconds=settings.JWT_REFRESH_TOKEN_EXPIRATION),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    refresh_token = jwt.encode(refresh_payload, settings.JWT_SECRET_KEY, algorithm='HS256')
    
    # Preparar la respuesta
    response_data = {
        "message": "Login exitoso",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "data": {
            "id": user.id,
            "email": user.email
        }
    }
    
    return Response(response_data, status=200)

@user_router.get("/", response=List[UserResponseSchema], auth=HeaderJWTAuth())
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
        raise HttpError(500, f"Error al obtener usuarios: {str(e)}")


@user_router.get("/{user_id}", response={200: UserResponseSchema, 404: ErrorResponseSchema}, auth=HeaderJWTAuth())
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


@user_router.put("/{user_id}", response={200: UserResponseSchema, 404: ErrorResponseSchema, 400: ErrorResponseSchema}, auth=HeaderJWTAuth())
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


@user_router.delete("/{user_id}", response={200: SuccessResponseSchema, 404: ErrorResponseSchema}, auth=HeaderJWTAuth())
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

