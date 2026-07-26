import io
import json
import zipfile
from datetime import datetime
from typing import Any

import simplekml
from jinja2 import Environment
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session
from xhtml2pdf import pisa

from app.models.rda import Rda
from app.models.report_template import ReportTemplate
from app.services.form_validation import parse_fields
from app.services.report_templates_default import (
    DEFAULT_CONSOLIDATED_TEMPLATE,
    DEFAULT_SINGLE_TEMPLATE,
)

_jinja_env = Environment(autoescape=True)


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%d/%m/%Y %H:%M")


def _format_value(value: Any) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "-"
    return str(value)


def build_field_rows(rda: Rda) -> list[dict[str, str]]:
    fields = parse_fields(rda.form_template_version.schema)
    rows = []
    for field in sorted(fields, key=lambda f: f.order):
        rows.append({"label": field.label, "value": _format_value(rda.answers.get(field.key))})
    return rows


def build_rda_context(rda: Rda) -> dict[str, Any]:
    return {
        "team_name": rda.team.name,
        "coletor_name": rda.submitted_by.name,
        "coordenador_name": rda.reviewed_by.name if rda.reviewed_by else None,
        "status": rda.status.value,
        "submitted_at": _format_datetime(rda.submitted_at),
        "reviewed_at": _format_datetime(rda.reviewed_at),
        "review_comment": rda.review_comment,
        "fields": build_field_rows(rda),
    }


def get_single_template_source(db: Session, contract_id) -> str:
    template = db.scalar(select(ReportTemplate).where(ReportTemplate.contract_id == contract_id))
    return template.html_template if template else DEFAULT_SINGLE_TEMPLATE


def render_single_rda_html(db: Session, rda: Rda) -> str:
    context = build_rda_context(rda)
    context.update(
        organization_name=rda.contract.organization.name,
        contract_name=rda.contract.name,
        generated_at=_format_datetime(datetime.now()),
    )
    template_source = get_single_template_source(db, rda.contract_id)
    return _jinja_env.from_string(template_source).render(**context)


def render_consolidated_html(
    db: Session, rdas: list[Rda], *, contract, period_label: str
) -> str:
    context = {
        "organization_name": contract.organization.name,
        "contract_name": contract.name,
        "period_label": period_label,
        "total_rdas": len(rdas),
        "generated_at": _format_datetime(datetime.now()),
        "rdas": [build_rda_context(rda) for rda in rdas],
    }
    return _jinja_env.from_string(DEFAULT_CONSOLIDATED_TEMPLATE).render(**context)


def html_to_pdf(html: str) -> bytes:
    buffer = io.BytesIO()
    result = pisa.CreatePDF(io.StringIO(html), dest=buffer)
    if result.err:
        raise RuntimeError("Falha ao gerar PDF a partir do HTML do relatorio")
    return buffer.getvalue()


def build_excel(rdas: list[Rda]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "RDAs"

    header = ["Equipe", "Coletor", "Status", "Enviado em", "Revisado em", "Campo", "Resposta"]
    ws.append(header)

    for rda in rdas:
        rows = build_field_rows(rda)
        base = [
            rda.team.name,
            rda.submitted_by.name,
            rda.status.value,
            _format_datetime(rda.submitted_at) or "-",
            _format_datetime(rda.reviewed_at) or "-",
        ]
        if not rows:
            ws.append(base + ["-", "-"])
        for row in rows:
            ws.append(base + [row["label"], row["value"]])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def build_csv(rdas: list[Rda]) -> bytes:
    lines = ["equipe,coletor,status,enviado_em,revisado_em,campo,resposta"]
    for rda in rdas:
        rows = build_field_rows(rda)
        base = [
            rda.team.name,
            rda.submitted_by.name,
            rda.status.value,
            _format_datetime(rda.submitted_at) or "",
            _format_datetime(rda.reviewed_at) or "",
        ]

        def esc(value: str) -> str:
            value = value.replace('"', '""')
            return f'"{value}"' if "," in value or '"' in value else value

        entries = rows or [{"label": "-", "value": "-"}]
        for row in entries:
            lines.append(",".join(esc(v) for v in [*base, row["label"], row["value"]]))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _extract_coordinates(rda: Rda) -> list[tuple[float, float]]:
    """Extrai lat/lng dos campos do tipo 'localizacao' respondidos como
    'lat,lng' (formato usado pelo app mobile, ver mobile/lib/widgets/dynamic_form.dart)."""
    fields = parse_fields(rda.form_template_version.schema)
    coords = []
    for field in fields:
        if field.type.value != "localizacao":
            continue
        value = rda.answers.get(field.key)
        if not value or "," not in str(value):
            continue
        try:
            lat_str, lng_str = str(value).split(",", 1)
            coords.append((float(lat_str.strip()), float(lng_str.strip())))
        except ValueError:
            continue
    return coords


def build_geojson(rdas: list[Rda]) -> dict[str, Any]:
    features = []
    for rda in rdas:
        for lat, lng in _extract_coordinates(rda):
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lng, lat]},
                    "properties": {
                        "rda_id": str(rda.id),
                        "equipe": rda.team.name,
                        "coletor": rda.submitted_by.name,
                        "status": rda.status.value,
                        "enviado_em": _format_datetime(rda.submitted_at),
                    },
                }
            )
    return {"type": "FeatureCollection", "features": features}


def build_kmz(rdas: list[Rda]) -> bytes:
    kml = simplekml.Kml()
    for rda in rdas:
        for lat, lng in _extract_coordinates(rda):
            point = kml.newpoint(
                name=f"RDA {rda.team.name} — {_format_datetime(rda.submitted_at) or ''}"
            )
            point.coords = [(lng, lat)]
            point.description = (
                f"Coletor: {rda.submitted_by.name}\nStatus: {rda.status.value}"
            )

    kml_bytes = kml.kml().encode("utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml_bytes)
    return buffer.getvalue()
