# api/common/schemas.py
from ninja import Schema
from pydantic import ConfigDict

class BaseSchema(Schema):
    """Todas las respuestas/entradas deben heredar de aquí."""
    model_config = ConfigDict(from_attributes=True)
