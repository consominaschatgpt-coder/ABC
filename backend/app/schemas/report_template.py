import uuid

from pydantic import BaseModel, ConfigDict


class ReportTemplateUpsert(BaseModel):
    name: str
    html_template: str


class ReportTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contract_id: uuid.UUID
    name: str
    html_template: str
