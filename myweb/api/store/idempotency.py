"""
Sistema de idempotencia para operaciones de store
"""
from functools import wraps
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from typing import Optional, Any
from .models import StoreIdempotencyRecord
import logging
logger = logging.getLogger(__name__)

IN_PROGRESS = 0  # estado provisional antes de saber el resultado


def store_idempotent():
    """
    Decorador para vistas/servicios. Guarda y devuelve la misma respuesta
    cuando llega el mismo request (mismo user+key+path+method).
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(request, *args, **kwargs):
            key = (
                request.headers.get("Idempotency-Key")
                or request.headers.get("HTTP_IDEMPOTENCY_KEY")
                or kwargs.get("key")
            )
            if not key:
                raise ValidationError("MISSING_IDEMPOTENCY_KEY")

            key = str(key).strip()
            if len(key) > 64:
                raise ValidationError("KEY_TOO_LONG")

            lookup = dict(
                key   = key,
                user  = getattr(request, "user", None),
                path  = request.path,
                method= request.method,
            )
            # ¿Ya existe?
            record = StoreIdempotencyRecord.objects.filter(**lookup).first()
            if record:
                return record.status, record.response

            # Nueva operación
            try:
                with transaction.atomic():
                    record = StoreIdempotencyRecord.objects.create(**lookup,
                                                                   status=IN_PROGRESS,
                                                                   response={})
            except IntegrityError:
                # Otro hilo la creó – leerla
                record = StoreIdempotencyRecord.objects.get(**lookup)
                return record.status, record.response

            # Ejecutar función original
            if request.method in ("GET", "HEAD"):
                # Para operaciones de solo lectura no necesitamos idempotencia
                return fn(request, *args, **kwargs)

            status, resp = fn(request, *args, **kwargs)

            # Guardar resultado definitivo
            record.status, record.response = status, resp
            record.save(update_fields=["status", "response"])
            logger.info("idempotency_saved", extra=lookup)
            return status, resp
        return wrapper
    return decorator