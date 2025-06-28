# api/common/schemas.py
from ninja import Schema

class BaseSchema(Schema):
    """Todas las respuestas/entradas deben heredar de aquí."""
    model_config = {"from_attributes": True}
