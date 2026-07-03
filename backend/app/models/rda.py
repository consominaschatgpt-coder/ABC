import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase


class RdaStatus(str, enum.Enum):
    RASCUNHO = "rascunho"
    ENVIADO = "enviado"
    EM_REVISAO = "em_revisao"
    APROVADO = "aprovado"
    REPROVADO = "reprovado"


class RdaAuditAction(str, enum.Enum):
    CRIADO = "criado"
    EDITADO = "editado"
    ENVIADO = "enviado"
    INICIADA_REVISAO = "iniciada_revisao"
    APROVADO = "aprovado"
    REPROVADO = "reprovado"


class Rda(TimestampedBase):
    """Relatorio Diario de Atividades preenchido por um coletor em campo."""

    __tablename__ = "rdas"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE")
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE")
    )
    form_template_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("form_template_versions.id", ondelete="RESTRICT")
    )
    submitted_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )

    status: Mapped[RdaStatus] = mapped_column(
        Enum(RdaStatus, name="rda_status"), default=RdaStatus.RASCUNHO
    )

    # Respostas tal como enviadas pela primeira vez (imutavel) e respostas
    # atuais (podem ser corrigidas pelo coordenador antes de aprovar).
    original_answers: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_comment: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    contract: Mapped["Contract"] = relationship()
    team: Mapped["Team"] = relationship()
    form_template_version: Mapped["FormTemplateVersion"] = relationship()
    submitted_by: Mapped["User"] = relationship(foreign_keys=[submitted_by_id])
    reviewed_by: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by_id])
    audit_logs: Mapped[list["RdaAuditLog"]] = relationship(
        back_populates="rda", cascade="all, delete-orphan", order_by="RdaAuditLog.created_at"
    )


class RdaAuditLog(TimestampedBase):
    """Trilha de auditoria: quem alterou o que, quando, e por que."""

    __tablename__ = "rda_audit_logs"

    rda_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rdas.id", ondelete="CASCADE")
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    action: Mapped[RdaAuditAction] = mapped_column(Enum(RdaAuditAction, name="rda_audit_action"))
    # Lista de {"field": key, "old_value": ..., "new_value": ...} quando action == editado
    field_changes: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    comment: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    rda: Mapped["Rda"] = relationship(back_populates="audit_logs")
    actor: Mapped["User"] = relationship()
