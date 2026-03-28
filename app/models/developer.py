import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db_base import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, generate_uuid


class Developer(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "developers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="developer",
        cascade="all, delete-orphan",
    )
