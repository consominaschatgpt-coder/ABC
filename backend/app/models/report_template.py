import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase


class ReportTemplate(TimestampedBase):
    """Layout do relatorio (HTML/Jinja2) de um contrato. Se o contrato nao
    tiver um registro aqui, usa-se o modelo padrao Consominas
    (ver app.services.report_service.DEFAULT_SINGLE_TEMPLATE)."""

    __tablename__ = "report_templates"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), unique=True
    )
    name: Mapped[str] = mapped_column(Text)
    html_template: Mapped[str] = mapped_column(Text)

    contract: Mapped["Contract"] = relationship()
