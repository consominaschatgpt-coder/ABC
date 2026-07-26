import uuid

from fastapi import HTTPException
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.rda import Rda
from app.models.team import team_assignments
from app.models.user import Role, User

"""Regras de visibilidade de RDA, compartilhadas entre app/api/routes/rdas.py
e app/api/routes/reports.py — um relatorio nao pode vazar dados que o
usuario nao teria acesso via a API de RDA."""


def is_assigned_to_team(db: Session, user: User, team_id: uuid.UUID) -> bool:
    return (
        db.execute(
            select(team_assignments).where(
                team_assignments.c.user_id == user.id,
                team_assignments.c.team_id == team_id,
            )
        ).first()
        is not None
    )


def ensure_can_view(db: Session, user: User, rda: Rda) -> None:
    if user.role in (Role.ADMIN, Role.GESTOR):
        return
    if user.role == Role.COORDENADOR and is_assigned_to_team(db, user, rda.team_id):
        return
    if user.role == Role.COLETOR and rda.submitted_by_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Voce nao tem acesso a este RDA")


def ensure_can_review(db: Session, user: User, rda: Rda) -> None:
    if user.role == Role.ADMIN:
        return
    if user.role == Role.COORDENADOR and is_assigned_to_team(db, user, rda.team_id):
        return
    raise HTTPException(status_code=403, detail="Voce nao e responsavel por esta equipe/contrato")


def scope_list_query(query: Select, db: Session, user: User) -> Select:
    if user.role in (Role.ADMIN, Role.GESTOR):
        return query
    if user.role == Role.COORDENADOR:
        my_teams = select(team_assignments.c.team_id).where(
            team_assignments.c.user_id == user.id
        )
        return query.where(Rda.team_id.in_(my_teams))
    if user.role == Role.COLETOR:
        return query.where(Rda.submitted_by_id == user.id)
    raise HTTPException(status_code=403, detail="Voce nao tem acesso a RDAs")
