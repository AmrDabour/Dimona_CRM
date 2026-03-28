import uuid
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db_base import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, generate_uuid


class Project(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )
    developer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("developers.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 8), nullable=True)
    lng: Mapped[Decimal | None] = mapped_column(Numeric(11, 8), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    brochure_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    developer: Mapped["Developer"] = relationship(
        "Developer",
        back_populates="projects",
    )
    units: Mapped[list["Unit"]] = relationship(
        "Unit",
        back_populates="project",
        cascade="all, delete-orphan",
    )
