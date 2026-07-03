import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.contract import Contract
from app.models.user import Role
from app.schemas.contract import ContractCreate, ContractRead

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("", response_model=ContractRead, status_code=status.HTTP_201_CREATED)
def create_contract(
    payload: ContractCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN)),
) -> Contract:
    contract = Contract(name=payload.name, organization_id=payload.organization_id)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


@router.get("", response_model=list[ContractRead])
def list_contracts(
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN, Role.GESTOR, Role.COORDENADOR)),
) -> list[Contract]:
    return list(db.scalars(select(Contract)))


@router.get("/{contract_id}", response_model=ContractRead)
def get_contract(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.ADMIN, Role.GESTOR, Role.COORDENADOR)),
) -> Contract:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contrato nao encontrado")
    return contract
