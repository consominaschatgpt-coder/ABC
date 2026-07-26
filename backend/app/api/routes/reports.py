import json
import uuid
from datetime import date, datetime, time
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.contract import Contract
from app.models.rda import Rda, RdaStatus
from app.models.report_template import ReportTemplate
from app.models.user import Role, User
from app.schemas.report_template import ReportTemplateRead, ReportTemplateUpsert
from app.services import report_service
from app.services.rda_access import ensure_can_view, scope_list_query

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    GEOJSON = "geojson"
    KMZ = "kmz"


MEDIA_TYPES = {
    ReportFormat.PDF: "application/pdf",
    ReportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ReportFormat.CSV: "text/csv",
    ReportFormat.GEOJSON: "application/geo+json",
    ReportFormat.KMZ: "application/vnd.google-earth.kmz",
}


def _get_rda_or_404(db: Session, rda_id: uuid.UUID) -> Rda:
    rda = db.get(Rda, rda_id)
    if rda is None:
        raise HTTPException(status_code=404, detail="RDA nao encontrado")
    return rda


def _ensure_approved(rda: Rda) -> None:
    if rda.status != RdaStatus.APROVADO:
        raise HTTPException(
            status_code=409,
            detail="So e possivel gerar relatorio de um RDA aprovado",
        )


@router.get("/rdas/{rda_id}/pdf")
def get_rda_report_pdf(
    rda_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    rda = _get_rda_or_404(db, rda_id)
    ensure_can_view(db, current_user, rda)
    _ensure_approved(rda)

    html = report_service.render_single_rda_html(db, rda)
    pdf_bytes = report_service.html_to_pdf(html)
    return Response(content=pdf_bytes, media_type=MEDIA_TYPES[ReportFormat.PDF])


@router.get("/rdas/{rda_id}/excel")
def get_rda_report_excel(
    rda_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    rda = _get_rda_or_404(db, rda_id)
    ensure_can_view(db, current_user, rda)
    _ensure_approved(rda)

    excel_bytes = report_service.build_excel([rda])
    return Response(content=excel_bytes, media_type=MEDIA_TYPES[ReportFormat.EXCEL])


@router.get("/consolidated")
def get_consolidated_report(
    contract_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
    format: ReportFormat = ReportFormat.PDF,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Consolida os RDAs aprovados de um contrato (opcionalmente filtrando
    por periodo de envio), no formato pedido. Reflete o mesmo escopo de
    visibilidade por papel usado em GET /rdas."""
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contrato nao encontrado")

    query = scope_list_query(select(Rda), db, current_user)
    query = query.where(Rda.contract_id == contract_id, Rda.status == RdaStatus.APROVADO)
    if date_from is not None:
        query = query.where(Rda.submitted_at >= datetime.combine(date_from, time.min))
    if date_to is not None:
        query = query.where(Rda.submitted_at <= datetime.combine(date_to, time.max))
    query = query.order_by(Rda.submitted_at)

    rdas = list(db.scalars(query))

    if date_from and date_to:
        period_label = f"{date_from.strftime('%d/%m/%Y')} a {date_to.strftime('%d/%m/%Y')}"
    elif date_from:
        period_label = f"a partir de {date_from.strftime('%d/%m/%Y')}"
    elif date_to:
        period_label = f"ate {date_to.strftime('%d/%m/%Y')}"
    else:
        period_label = "todo o periodo"

    if format == ReportFormat.PDF:
        html = report_service.render_consolidated_html(
            db, rdas, contract=contract, period_label=period_label
        )
        content = report_service.html_to_pdf(html)
    elif format == ReportFormat.EXCEL:
        content = report_service.build_excel(rdas)
    elif format == ReportFormat.CSV:
        content = report_service.build_csv(rdas)
    elif format == ReportFormat.GEOJSON:
        content = json.dumps(report_service.build_geojson(rdas)).encode("utf-8")
    elif format == ReportFormat.KMZ:
        content = report_service.build_kmz(rdas)
    else:  # pragma: no cover - Enum ja restringe os valores possiveis
        raise HTTPException(status_code=400, detail="Formato invalido")

    return Response(content=content, media_type=MEDIA_TYPES[format])


@router.get("/templates/{contract_id}", response_model=ReportTemplateRead | None)
def get_report_template(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN, Role.GESTOR, Role.COORDENADOR)),
) -> ReportTemplate | None:
    return db.scalar(select(ReportTemplate).where(ReportTemplate.contract_id == contract_id))


@router.put("/templates/{contract_id}", response_model=ReportTemplateRead)
def upsert_report_template(
    contract_id: uuid.UUID,
    payload: ReportTemplateUpsert,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN)),
) -> ReportTemplate:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contrato nao encontrado")

    template = db.scalar(select(ReportTemplate).where(ReportTemplate.contract_id == contract_id))
    if template is None:
        template = ReportTemplate(contract_id=contract_id, name=payload.name, html_template=payload.html_template)
        db.add(template)
    else:
        template.name = payload.name
        template.html_template = payload.html_template

    db.commit()
    db.refresh(template)
    return template
