# api/products/pagination.py
from ninja.pagination import LimitOffsetPagination
from pydantic import BaseModel, Field
from typing import Optional, List, Any

class DefaultPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit     = 100

class PaginationParams(BaseModel):
    limit: Optional[int] = Field(20, ge=1, le=100)
    offset: Optional[int] = Field(0, ge=0)

def paginate_response(data: List[Any], pagination: PaginationParams):
    """
    Implementa paginación simple para listas de datos
    """
    limit = pagination.limit or 20
    offset = pagination.offset or 0
    
    # Aplicar paginación
    paginated_data = data[offset:offset + limit]
    
    # Calcular información de paginación
    total_count = len(data)
    total_pages = (total_count + limit - 1) // limit
    current_page = (offset // limit) + 1
    
    return {
        "results": paginated_data,
        "count": total_count,
        "next": f"?limit={limit}&offset={offset + limit}" if offset + limit < total_count else None,
        "previous": f"?limit={limit}&offset={offset - limit}" if offset > 0 else None,
        "current_page": current_page,
        "total_pages": total_pages
    }
