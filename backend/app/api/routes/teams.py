import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.team import Team, team_assignments
from app.models.user import Role, User
from app.schemas.team import TeamCreate, TeamMemberAdd, TeamRead
from app.schemas.user import UserRead

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN)),
) -> Team:
    team = Team(name=payload.name, contract_id=payload.contract_id)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("", response_model=list[TeamRead])
def list_teams(
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN, Role.GESTOR, Role.COORDENADOR)),
) -> list[Team]:
    return list(db.scalars(select(Team)))


@router.get("/{team_id}", response_model=TeamRead)
def get_team(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN, Role.GESTOR, Role.COORDENADOR)),
) -> Team:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Equipe nao encontrada")
    return team


def _get_team_or_404(db: Session, team_id: uuid.UUID) -> Team:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Equipe nao encontrada")
    return team


@router.get("/{team_id}/members", response_model=list[UserRead])
def list_team_members(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN, Role.GESTOR, Role.COORDENADOR)),
) -> list[User]:
    team = _get_team_or_404(db, team_id)
    return team.members


@router.post("/{team_id}/members", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def add_team_member(
    team_id: uuid.UUID,
    payload: TeamMemberAdd,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN)),
) -> User:
    team = _get_team_or_404(db, team_id)
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    try:
        db.execute(insert(team_assignments).values(user_id=user.id, team_id=team.id))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Usuario ja pertence a essa equipe")
    return user


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN)),
) -> None:
    _get_team_or_404(db, team_id)
    db.execute(
        delete(team_assignments).where(
            team_assignments.c.team_id == team_id, team_assignments.c.user_id == user_id
        )
    )
    db.commit()
