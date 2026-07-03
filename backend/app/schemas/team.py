import uuid

from pydantic import BaseModel, ConfigDict


class TeamCreate(BaseModel):
    name: str
    contract_id: uuid.UUID


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    contract_id: uuid.UUID


class TeamMemberAdd(BaseModel):
    user_id: uuid.UUID
