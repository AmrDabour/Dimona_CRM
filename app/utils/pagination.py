from typing import TypeVar, Generic, List
from pydantic import BaseModel
import math

T = TypeVar("T")


def paginate(
    items: List[T],
    total: int,
    page: int,
    page_size: int,
) -> dict:
    """Create a paginated response dictionary."""
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }
