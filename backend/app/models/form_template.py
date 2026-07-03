import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase


class FormTemplate(TimestampedBase):
    """Modelo de RDA configuravel por contrato. O conteudo dos campos vive nas
    FormTemplateVersion, para que editar o formulario nao afete RDAs antigos."""

    __tablename__ = "form_templates"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255))

    contract: Mapped["Contract"] = relationship()
    versions: Mapped[list["FormTemplateVersion"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="FormTemplateVersion.version_number",
    )


class FormTemplateVersion(TimestampedBase):
    """Versao imutavel do formulario: uma vez publicada, RDAs passam a
    referenciar essa versao especifica pelo id."""

    __tablename__ = "form_template_versions"
    __table_args__ = (
        UniqueConstraint("template_id", "version_number", name="uq_template_version_number"),
        Index(
            "uq_one_published_version_per_template",
            "template_id",
            unique=True,
            postgresql_where=text("is_published = true"),
        ),
    )

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("form_templates.id", ondelete="CASCADE")
    )
    version_number: Mapped[int] = mapped_column(Integer)
    # Lista de definicoes de campo (ver app.schemas.form_template.FieldDefinition)
    schema: Mapped[list[dict]] = mapped_column(JSONB)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    template: Mapped["FormTemplate"] = relationship(back_populates="versions")
