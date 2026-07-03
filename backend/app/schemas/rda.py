import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.rda import RdaAuditAction, RdaStatus


class RdaCreate(BaseModel):
    contract_id: uuid.UUID
    team_id: uuid.UUID
    form_template_version_id: uuid.UUID
    answers: dict[str, Any] = Field(default_factory=dict)


class RdaAnswersUpdate(BaseModel):
    answers: dict[str, Any]
    comment: str | None = None


class RdaRejectRequest(BaseModel):
    reason: str


class RdaApproveRequest(BaseModel):
    comment: str | None = None


class RdaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contract_id: uuid.UUID
    team_id: uuid.UUID
    form_template_version_id: uuid.UUID
    submitted_by_id: uuid.UUID
    status: RdaStatus
    original_answers: dict[str, Any] | None
    answers: dict[str, Any]
    submitted_at: datetime | None
    reviewed_by_id: uuid.UUID | None
    reviewed_at: datetime | None
    review_comment: str | None
    created_at: datetime
    updated_at: datetime


class RdaAuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID
    action: RdaAuditAction
    field_changes: list[dict[str, Any]] | None
    comment: str | None
    created_at: datetime
