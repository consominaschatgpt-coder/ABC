import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.form_template import FormTemplateVersion
from app.models.rda import Rda, RdaAuditAction, RdaAuditLog, RdaStatus
from app.models.team import team_assignments
from app.models.user import Role, User
from app.schemas.rda import (
    RdaAnswersUpdate,
    RdaApproveRequest,
    RdaAuditLogRead,
    RdaCreate,
    RdaRead,
    RdaRejectRequest,
)
from app.services.form_validation import (
    compute_answer_diff,
    parse_fields,
    validate_answer_values,
    validate_required_fields,
)

router = APIRouter(prefix="/rdas", tags=["rdas"])

EDITABLE_BY_COLETOR = (RdaStatus.RASCUNHO, RdaStatus.REPROVADO)
EDITABLE_BY_REVIEWER = (RdaStatus.ENVIADO, RdaStatus.EM_REVISAO)


def _get_rda_or_404(db: Session, rda_id: uuid.UUID) -> Rda:
    rda = db.get(Rda, rda_id)
    if rda is None:
        raise HTTPException(status_code=404, detail="RDA nao encontrado")
    return rda


def _is_assigned_to_team(db: Session, user: User, team_id: uuid.UUID) -> bool:
    return (
        db.execute(
            select(team_assignments).where(
                team_assignments.c.user_id == user.id,
                team_assignments.c.team_id == team_id,
            )
        ).first()
        is not None
    )


def _ensure_can_view(db: Session, user: User, rda: Rda) -> None:
    if user.role in (Role.ADMIN, Role.GESTOR):
        return
    if user.role == Role.COORDENADOR and _is_assigned_to_team(db, user, rda.team_id):
        return
    if user.role == Role.COLETOR and rda.submitted_by_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Voce nao tem acesso a este RDA")


def _ensure_can_edit_as_owner(user: User, rda: Rda) -> None:
    if user.role == Role.ADMIN:
        return
    if rda.submitted_by_id != user.id:
        raise HTTPException(status_code=403, detail="Este RDA nao pertence a voce")


def _ensure_can_review(db: Session, user: User, rda: Rda) -> None:
    if user.role == Role.ADMIN:
        return
    if user.role == Role.COORDENADOR and _is_assigned_to_team(db, user, rda.team_id):
        return
    raise HTTPException(
        status_code=403, detail="Voce nao e responsavel por esta equipe/contrato"
    )


def _add_audit_log(
    db: Session,
    rda: Rda,
    actor: User,
    action: RdaAuditAction,
    field_changes: list[dict] | None = None,
    comment: str | None = None,
) -> None:
    db.add(
        RdaAuditLog(
            rda_id=rda.id,
            actor_id=actor.id,
            action=action,
            field_changes=field_changes,
            comment=comment,
        )
    )


def _get_template_fields(db: Session, form_template_version_id: uuid.UUID) -> list:
    version = db.get(FormTemplateVersion, form_template_version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Versao de formulario nao encontrada")
    return parse_fields(version.schema)


@router.post("", response_model=RdaRead, status_code=status.HTTP_201_CREATED)
def create_rda(
    payload: RdaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.COLETOR)),
) -> Rda:
    if current_user.role == Role.COLETOR and not _is_assigned_to_team(
        db, current_user, payload.team_id
    ):
        raise HTTPException(status_code=403, detail="Voce nao pertence a essa equipe")

    fields = _get_template_fields(db, payload.form_template_version_id)
    errors = validate_answer_values(fields, payload.answers)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    rda = Rda(
        contract_id=payload.contract_id,
        team_id=payload.team_id,
        form_template_version_id=payload.form_template_version_id,
        submitted_by_id=current_user.id,
        status=RdaStatus.RASCUNHO,
        answers=payload.answers,
    )
    db.add(rda)
    db.flush()
    _add_audit_log(db, rda, current_user, RdaAuditAction.CRIADO)
    db.commit()
    db.refresh(rda)
    return rda


@router.get("", response_model=list[RdaRead])
def list_rdas(
    status_filter: RdaStatus | None = None,
    contract_id: uuid.UUID | None = None,
    team_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Rda]:
    query = select(Rda)

    if current_user.role in (Role.ADMIN, Role.GESTOR):
        pass
    elif current_user.role == Role.COORDENADOR:
        my_teams = select(team_assignments.c.team_id).where(
            team_assignments.c.user_id == current_user.id
        )
        query = query.where(Rda.team_id.in_(my_teams))
    elif current_user.role == Role.COLETOR:
        query = query.where(Rda.submitted_by_id == current_user.id)
    else:
        raise HTTPException(status_code=403, detail="Voce nao tem acesso a RDAs")

    if status_filter is not None:
        query = query.where(Rda.status == status_filter)
    if contract_id is not None:
        query = query.where(Rda.contract_id == contract_id)
    if team_id is not None:
        query = query.where(Rda.team_id == team_id)

    return list(db.scalars(query))


@router.get("/{rda_id}", response_model=RdaRead)
def get_rda(
    rda_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Rda:
    rda = _get_rda_or_404(db, rda_id)
    _ensure_can_view(db, current_user, rda)
    return rda


@router.get("/{rda_id}/audit-log", response_model=list[RdaAuditLogRead])
def get_rda_audit_log(
    rda_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RdaAuditLog]:
    rda = _get_rda_or_404(db, rda_id)
    _ensure_can_view(db, current_user, rda)
    return rda.audit_logs


@router.patch("/{rda_id}/answers", response_model=RdaRead)
def update_rda_answers(
    rda_id: uuid.UUID,
    payload: RdaAnswersUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Rda:
    rda = _get_rda_or_404(db, rda_id)

    if current_user.role == Role.COLETOR:
        _ensure_can_edit_as_owner(current_user, rda)
        if rda.status not in EDITABLE_BY_COLETOR:
            raise HTTPException(
                status_code=409,
                detail="RDA so pode ser editado pelo coletor em rascunho ou reprovado",
            )
    elif current_user.role in (Role.ADMIN, Role.COORDENADOR):
        _ensure_can_review(db, current_user, rda)
        if rda.status not in EDITABLE_BY_REVIEWER:
            raise HTTPException(
                status_code=409,
                detail="RDA so pode ser corrigido pelo coordenador quando enviado ou em revisao",
            )
    else:
        raise HTTPException(status_code=403, detail="Voce nao pode editar este RDA")

    fields = _get_template_fields(db, rda.form_template_version_id)
    merged_answers = {**rda.answers, **payload.answers}
    errors = validate_answer_values(fields, merged_answers)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    diff = compute_answer_diff(rda.answers, merged_answers)
    if diff:
        rda.answers = merged_answers
        _add_audit_log(
            db, rda, current_user, RdaAuditAction.EDITADO, field_changes=diff, comment=payload.comment
        )
        db.commit()
        db.refresh(rda)
    return rda


@router.post("/{rda_id}/submit", response_model=RdaRead)
def submit_rda(
    rda_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Rda:
    rda = _get_rda_or_404(db, rda_id)
    if current_user.role not in (Role.ADMIN, Role.COLETOR):
        raise HTTPException(status_code=403, detail="Voce nao pode enviar este RDA")
    _ensure_can_edit_as_owner(current_user, rda)

    if rda.status not in EDITABLE_BY_COLETOR:
        raise HTTPException(
            status_code=409, detail="Apenas RDAs em rascunho ou reprovados podem ser enviados"
        )

    fields = _get_template_fields(db, rda.form_template_version_id)
    errors = validate_required_fields(fields, rda.answers)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    if rda.original_answers is None:
        rda.original_answers = rda.answers

    rda.status = RdaStatus.ENVIADO
    rda.submitted_at = datetime.now(timezone.utc)
    _add_audit_log(db, rda, current_user, RdaAuditAction.ENVIADO)
    db.commit()
    db.refresh(rda)
    return rda


@router.post("/{rda_id}/start-review", response_model=RdaRead)
def start_review(
    rda_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Rda:
    rda = _get_rda_or_404(db, rda_id)
    _ensure_can_review(db, current_user, rda)

    if rda.status != RdaStatus.ENVIADO:
        raise HTTPException(status_code=409, detail="Apenas RDAs enviados podem entrar em revisao")

    rda.status = RdaStatus.EM_REVISAO
    _add_audit_log(db, rda, current_user, RdaAuditAction.INICIADA_REVISAO)
    db.commit()
    db.refresh(rda)
    return rda


@router.post("/{rda_id}/approve", response_model=RdaRead)
def approve_rda(
    rda_id: uuid.UUID,
    payload: RdaApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Rda:
    rda = _get_rda_or_404(db, rda_id)
    _ensure_can_review(db, current_user, rda)

    if rda.status not in (RdaStatus.ENVIADO, RdaStatus.EM_REVISAO):
        raise HTTPException(status_code=409, detail="RDA nao esta em um estado aprovavel")

    rda.status = RdaStatus.APROVADO
    rda.reviewed_by_id = current_user.id
    rda.reviewed_at = datetime.now(timezone.utc)
    rda.review_comment = payload.comment
    _add_audit_log(db, rda, current_user, RdaAuditAction.APROVADO, comment=payload.comment)
    db.commit()
    db.refresh(rda)
    return rda


@router.post("/{rda_id}/reject", response_model=RdaRead)
def reject_rda(
    rda_id: uuid.UUID,
    payload: RdaRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Rda:
    rda = _get_rda_or_404(db, rda_id)
    _ensure_can_review(db, current_user, rda)

    if rda.status not in (RdaStatus.ENVIADO, RdaStatus.EM_REVISAO):
        raise HTTPException(status_code=409, detail="RDA nao esta em um estado reprovavel")

    rda.status = RdaStatus.REPROVADO
    rda.reviewed_by_id = current_user.id
    rda.reviewed_at = datetime.now(timezone.utc)
    rda.review_comment = payload.reason
    _add_audit_log(db, rda, current_user, RdaAuditAction.REPROVADO, comment=payload.reason)
    db.commit()
    db.refresh(rda)
    return rda
