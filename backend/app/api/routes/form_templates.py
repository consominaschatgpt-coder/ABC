import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.form_template import FormTemplate, FormTemplateVersion
from app.models.user import Role
from app.schemas.form_template import (
    FormTemplateCreate,
    FormTemplateRead,
    FormTemplateVersionCreate,
    FormTemplateVersionRead,
    FormTemplateWithCurrentVersion,
)

router = APIRouter(prefix="/form-templates", tags=["form-templates"])

READ_ROLES = (Role.ADMIN, Role.GESTOR, Role.COORDENADOR, Role.COLETOR)


def _get_template_or_404(db: Session, template_id: uuid.UUID) -> FormTemplate:
    template = db.get(FormTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Modelo de formulario nao encontrado")
    return template


def _current_version(template: FormTemplate) -> FormTemplateVersion | None:
    return next((v for v in template.versions if v.is_published), None)


@router.post("", response_model=FormTemplateRead, status_code=status.HTTP_201_CREATED)
def create_form_template(
    payload: FormTemplateCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN)),
) -> FormTemplate:
    template = FormTemplate(name=payload.name, contract_id=payload.contract_id)
    db.add(template)
    db.flush()

    version = FormTemplateVersion(
        template_id=template.id,
        version_number=1,
        schema=[f.model_dump(mode="json") for f in payload.fields],
        is_published=False,
    )
    db.add(version)
    db.commit()
    db.refresh(template)
    return template


@router.get("", response_model=list[FormTemplateRead])
def list_form_templates(
    contract_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN, Role.GESTOR, Role.COORDENADOR)),
) -> list[FormTemplate]:
    query = select(FormTemplate)
    if contract_id is not None:
        query = query.where(FormTemplate.contract_id == contract_id)
    return list(db.scalars(query))


@router.get("/{template_id}", response_model=FormTemplateWithCurrentVersion)
def get_form_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*READ_ROLES)),
) -> FormTemplateWithCurrentVersion:
    template = _get_template_or_404(db, template_id)
    return FormTemplateWithCurrentVersion(
        id=template.id,
        contract_id=template.contract_id,
        name=template.name,
        created_at=template.created_at,
        current_version=_current_version(template),
    )


@router.get("/{template_id}/versions", response_model=list[FormTemplateVersionRead])
def list_form_template_versions(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*READ_ROLES)),
) -> list[FormTemplateVersion]:
    template = _get_template_or_404(db, template_id)
    return template.versions


@router.post(
    "/{template_id}/versions",
    response_model=FormTemplateVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_form_template_version(
    template_id: uuid.UUID,
    payload: FormTemplateVersionCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN)),
) -> FormTemplateVersion:
    template = _get_template_or_404(db, template_id)
    next_number = max((v.version_number for v in template.versions), default=0) + 1

    version = FormTemplateVersion(
        template_id=template.id,
        version_number=next_number,
        schema=[f.model_dump(mode="json") for f in payload.fields],
        is_published=False,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.get("/{template_id}/versions/{version_id}", response_model=FormTemplateVersionRead)
def get_form_template_version(
    template_id: uuid.UUID,
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*READ_ROLES)),
) -> FormTemplateVersion:
    version = db.get(FormTemplateVersion, version_id)
    if version is None or version.template_id != template_id:
        raise HTTPException(status_code=404, detail="Versao de formulario nao encontrada")
    return version


@router.post(
    "/{template_id}/versions/{version_id}/publish", response_model=FormTemplateVersionRead
)
def publish_form_template_version(
    template_id: uuid.UUID,
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN)),
) -> FormTemplateVersion:
    version = db.get(FormTemplateVersion, version_id)
    if version is None or version.template_id != template_id:
        raise HTTPException(status_code=404, detail="Versao de formulario nao encontrada")

    for other in version.template.versions:
        if other.id != version.id and other.is_published:
            other.is_published = False
            other.published_at = None
    db.flush()  # evita colidir com o indice unico parcial ao publicar a nova versao

    version.is_published = True
    version.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(version)
    return version
