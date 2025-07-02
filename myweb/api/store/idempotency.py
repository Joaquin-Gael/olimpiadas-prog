import functools, logging
from django.db import transaction
from django.utils import timezone
from ninja.errors import HttpError
from .models import StoreIdempotencyRecord

logger = logging.getLogger(__name__)

_HEADER = "HTTP_IDEMPOTENCY_KEY"  # Django transforma headers a esta forma

def store_idempotent(timeout_sec: int = 24*3600):
    """
    • Busca un registro previo → devuelve cache.
    • Si no existe → ejecuta la vista dentro de una TX,
      guarda la respuesta y la retorna.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapper(request, *args, **kwargs):
            key = request.META.get(_HEADER)
            if not key:
                raise HttpError(400, "Missing Idempotency-Key header")

            lookup = dict(
                key    = key,
                user   = request.user,
                method = request.method,
                path   = request.path,
            )

            try:
                rec = StoreIdempotencyRecord.objects.get(**lookup)
                age = (timezone.now() - rec.created_at).total_seconds()
                if age < timeout_sec:
                    logger.info("Idempotency HIT %s", key)
                    return rec.status, rec.response
                rec.delete()
            except StoreIdempotencyRecord.DoesNotExist:
                pass

            with transaction.atomic():
                status, resp = view_func(request, *args, **kwargs)
                StoreIdempotencyRecord.objects.create(
                    **lookup, status=status, response=resp
                )
            logger.info("Idempotency MISS %s → guardado", key)
            return status, resp
        return _wrapper
    return decorator 