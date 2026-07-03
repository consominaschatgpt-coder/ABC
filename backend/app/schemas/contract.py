import uuid

from pydantic import BaseModel, ConfigDict


class ContractCreate(BaseModel):
    name: str
    organization_id: uuid.UUID


class ContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    organization_id: uuid.UUID
