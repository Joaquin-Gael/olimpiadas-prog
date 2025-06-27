# api/products/pagination.py
from ninja.pagination import LimitOffsetPagination

class DefaultPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit     = 100
