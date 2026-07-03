import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SELECTION_TYPES = {"selecao_unica", "selecao_multipla"}


class FieldType(str, enum.Enum):
    TEXTO = "texto"
    NUMERO = "numero"
    DATA_HORA = "data_hora"
    SELECAO_UNICA = "selecao_unica"
    SELECAO_MULTIPLA = "selecao_multipla"
    FOTO = "foto"
    ASSINATURA = "assinatura"
    LOCALIZACAO = "localizacao"


class FieldCondition(BaseModel):
    """Condicao simples: o campo so aparece se `field` == `equals`."""

    field: str
    equals: str


class FieldDefinition(BaseModel):
    key: str
    label: str
    type: FieldType
    required: bool = False
    order: int = 0
    options: list[str] | None = None
    condition: FieldCondition | None = None

    @model_validator(mode="after")
    def _validate_options(self) -> "FieldDefinition":
        if self.type.value in SELECTION_TYPES and not self.options:
            raise ValueError(
                f"Campo '{self.key}': tipo '{self.type.value}' exige ao menos uma opcao"
            )
        return self


def _validate_field_list(fields: list[FieldDefinition]) -> list[FieldDefinition]:
    keys = [f.key for f in fields]
    if len(keys) != len(set(keys)):
        raise ValueError("As chaves (key) dos campos devem ser unicas")
    known_keys = set(keys)
    for f in fields:
        if f.condition and f.condition.field not in known_keys:
            raise ValueError(
                f"Condicao do campo '{f.key}' referencia campo inexistente "
                f"'{f.condition.field}'"
            )
    return fields


class FormTemplateVersionCreate(BaseModel):
    fields: list[FieldDefinition]

    _validate_fields = field_validator("fields")(_validate_field_list)


class FormTemplateVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    template_id: uuid.UUID
    version_number: int
    fields: list[FieldDefinition] = Field(validation_alias="schema")
    is_published: bool
    published_at: datetime | None
    created_at: datetime


class FormTemplateCreate(BaseModel):
    name: str
    contract_id: uuid.UUID
    fields: list[FieldDefinition]

    _validate_fields = field_validator("fields")(_validate_field_list)


class FormTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contract_id: uuid.UUID
    name: str
    created_at: datetime


class FormTemplateWithCurrentVersion(FormTemplateRead):
    current_version: FormTemplateVersionRead | None = None
