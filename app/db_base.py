"""Declarative base only — import this in models so Alembic need not load asyncpg."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
