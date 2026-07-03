import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedBase

# Associacao N:N entre usuarios e equipes: um coletor normalmente pertence a
# uma equipe, mas um coordenador/gestor pode ser responsavel por varias.
team_assignments = Table(
    "team_assignments",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("team_id", UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
)


class Team(TimestampedBase):
    """Equipe/frente de trabalho (ex.: por viatura), vinculada a um contrato."""

    __tablename__ = "teams"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255))

    contract: Mapped["Contract"] = relationship(back_populates="teams")
    members: Mapped[list["User"]] = relationship(
        secondary=team_assignments, back_populates="teams"
    )
