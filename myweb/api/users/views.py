from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings

from typing import List

from ninja import Router, Query, Schema, Form
from ninja.responses import Response
from ninja.errors import HttpError

from asgiref.sync import sync_to_async

from api.core.auth import JWTBearer, gen_token

from .models import Users
from .schemas import (
    UserRegistrationSchema,
    UserResponseSchema,
    UserUpdateSchema,
    UserLoginSchema,
    ErrorResponseSchema,
    SuccessResponseSchema,
    TokensResponseSchema, PasswordRecovery
)
from .services.services_notifications import UserNotificationsService

user_private_router = Router(
    tags=["Users"],
    auth=JWTBearer(),
)

user_public_router = Router(
    tags=["Users"],
)

@user_public_router.post("/forgot-password", summary="Solicitar recuperación de contraseña")
async def forgot_password(request, payload: PasswordRecovery):
    try:
        user = await sync_to_async(Users.objects.get)(email=payload.email)
    except Exception as e:
        return Response(status=200, content=True)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_link = f"{settings.DOMAIN}/reset-password?uid={uid}&token={token}"

    await UserNotificationsService.send_recovery_password(
        email=user.email,
        user=user,
        reset_url=reset_link
    )

    return Response(status=200, data=True)

@user_public_router.post("/reset-password", summary="Confirmar recuperación de contraseña")
async def reset_password(request, password1: str = Form(), password2: str = Form(), token: str = Query(), uid: str = Query()):
    from django.utils.http import urlsafe_base64_decode

    try:
        uid = urlsafe_base64_decode(uid).decode()
        user = Users.objects.get(pk=uid)
    except Exception:
        return {"ok": False, "detail": "Enlace inválido o expirado."}

    # 2. Verificar token
    if not default_token_generator.check_token(user, token):
        return {"ok": False, "detail": "Token inválido o expirado."}

    # 3. Validar y setear nueva contraseña
    if password1 != password2:
        return {"ok": False, "detail": "Las contraseñas no coinciden."}

    from django.contrib.auth.password_validation import validate_password
    try:
        validate_password(password1, user=user)
    except Exception as e:
        return {"ok": False, "detail": e.messages}


@user_public_router.post("/register", response={201: UserResponseSchema, 400: ErrorResponseSchema})
async def register_user(request, payload: UserRegistrationSchema):
    """
   Registra un nuevo usuario en el sistema.

   - Verifica que el email y el número de teléfono no estén previamente registrados.
   - Si las validaciones son exitosas, crea un nuevo usuario y devuelve su información (sin la contraseña).
   - En caso de error de duplicado o error en base de datos, devuelve un mensaje descriptivo con código 400.
   """
    try:
        # Verificar si el email ya existe
        if await sync_to_async(Users.objects.filter(email=payload.email).exists)():
            return Response(
                {"message": "El email ya está registrado", "detail": "Email duplicado"},
                status=400
            )
        
        # Verificar si el teléfono ya existe
        if await sync_to_async(Users.objects.filter(telephone=payload.telephone).exists)():
            return Response(
                {"message": "El teléfono ya está registrado", "detail": "Teléfono duplicado"},
                status=400
            )
        
        # Crear el usuario
        user = await sync_to_async(Users.objects.create_user)(
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            telephone=payload.telephone,
            password=payload.password,
            born_date=payload.born_date,
            state=payload.state
        )

        await UserNotificationsService.send_welcome(
            user=user,
            email=user.email,
        )
        
        # Retornar el usuario creado (sin password) y sin seguir el schema acordado
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

@transaction.atomic
@user_public_router.post("/login", response={200: TokensResponseSchema, 401: ErrorResponseSchema})
async def login_user(request, payload: UserLoginSchema):
    """
    Autentica un usuario utilizando email y contraseña.

    - Si las credenciales son válidas, retorna datos básicos del usuario.
    - Si el usuario no existe o las credenciales son incorrectas, responde con código 401.
    - También verifica si el usuario está activo antes de autorizar el acceso.
    """
    try:
        # Autenticar usuario
        user = await sync_to_async(authenticate)(request, email=payload.email, password=payload.password)
        
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

        user.last_login = timezone.now()

        await sync_to_async(user.save)()

        payload={
            "sub":str(user.id),
            "scopes": list(await sync_to_async(user.get_all_permissions)())
        }

        token = gen_token(payload=payload)
        _refresh_token = gen_token(payload=payload, refresh=True)
        
        return Response(
            {
                "message":"Login exitoso",
                "data":{
                    "access_token": token,
                    "refresh_token": _refresh_token,
                }
            },
            status=200
        )
        
    except Exception as e:
        return Response(
            {"message": "Error interno del servidor", "detail": str(e)},
            status=400
        )

@user_private_router.get("/", response=List[UserResponseSchema])
async def list_users(request):
    """
    Retorna una lista con todos los usuarios registrados en el sistema.

    - Los usuarios se ordenan por fecha de creación descendente.
    - En caso de error al acceder a la base de datos, devuelve un error 500 con el detalle.
    """
    try:
        users = await sync_to_async(
            lambda: list(Users.objects.all().order_by("-created_at")),
            thread_sensitive=True
        )()
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

@user_private_router.get("/refresh")
async def refresh_token(request):
    try:
        user = request.user

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

        payload={
            "sub":str(user.id),
            "scopes": list(await sync_to_async(user.get_all_permissions)())
        }

        token = gen_token(payload=payload)
        _refresh_token = gen_token(payload=payload, refresh=True)

        return Response(
            {
                "message":"Login exitoso",
                "data":{
                    "access_token": token,
                    "refresh_token": _refresh_token,
                }
            },
            status=200
        )

    except Exception as e:
        raise HttpError(500, f"Error al obtener usuarios: {str(e)}")

@user_private_router.get("/me", response={200:UserResponseSchema, 401: ErrorResponseSchema})
async def me_user(request):
    """
    Retorna un usuario en el sistema.

    - Param request: Metodo por el cual se obtiene info del cliente/browser
    - Return: UserResponseSchema
    """

    try:
        if request.user is None:
            return Response(ErrorResponseSchema(message="We cannot find user in this session", detail="Request-User = None"), status=401)

        return UserResponseSchema(
            id=request.user.id,
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            email=request.user.email,
            telephone=request.user.telephone,
            born_date=request.user.born_date,
            state=request.user.state,
            created_at=request.user.created_at,
            is_staff=request.user.is_staff
        )
    except Exception as e:
        return HttpError(500, f"Error al obtener usuarios: {str(e)}")


@user_private_router.get("/{user_id}", response={200: UserResponseSchema, 404: ErrorResponseSchema})
async def get_user(request, user_id: int):
    """
    Obtiene los datos de un usuario específico mediante su ID.

    - Si el usuario existe, retorna su información completa.
    - Si no se encuentra el usuario, retorna un mensaje de error con código 404.
    """
    try:
        user = await sync_to_async(Users.objects.get)(id=user_id)
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


@user_private_router.put("/{user_id}", response={200: UserResponseSchema, 404: ErrorResponseSchema, 400: ErrorResponseSchema})
def update_user(request, user_id: int, payload: UserUpdateSchema):
    """
    Actualiza los datos de un usuario específico.

    - Solo se actualizan los campos enviados (parcial).
    - Si el teléfono ya está en uso por otro usuario, devuelve un error 400.
    - Si el usuario no existe, devuelve un error 404.
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


@user_private_router.delete("/{user_id}", response={200: SuccessResponseSchema, 404: ErrorResponseSchema})
def delete_user(request, user_id: int):
    """
    Elimina completamente un usuario por su ID.

    - Si el usuario existe, lo elimina de la base de datos y devuelve un mensaje de éxito.
    - Si no se encuentra el usuario, responde con un error 404.
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