import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase


class Contract(TimestampedBase):
    """Contrato/cliente (ex.: MRN, Vale, Samarco). Formularios e modelos de
    relatorio variam por contrato."""

    __tablename__ = "contracts"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255))

    organization: Mapped["Organization"] = relationship(back_populates="contracts")
    teams: Mapped[list["Team"]] = relationship(
        back_populates="contract", cascade="all, delete-orphan"
    )
