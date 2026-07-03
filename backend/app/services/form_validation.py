from typing import Any

from app.schemas.form_template import FieldDefinition, FieldType

SELECTION_TYPES = {FieldType.SELECAO_UNICA, FieldType.SELECAO_MULTIPLA}


def parse_fields(schema: list[dict]) -> list[FieldDefinition]:
    return [FieldDefinition(**f) for f in schema]


def is_field_active(field: FieldDefinition, answers: dict[str, Any]) -> bool:
    """Um campo condicional so e considerado ativo (e portanto obrigatorio,
    se for o caso) quando a condicao e satisfeita."""
    if field.condition is None:
        return True
    return str(answers.get(field.condition.field)) == field.condition.equals


def validate_answer_values(fields: list[FieldDefinition], answers: dict[str, Any]) -> list[str]:
    """Valida tipos/opcoes das respostas presentes. Nao exige presenca de
    campos obrigatorios (ver validate_required_fields, usado so no envio)."""
    errors: list[str] = []
    fields_by_key = {f.key: f for f in fields}

    for key in answers:
        if key not in fields_by_key:
            errors.append(f"Campo desconhecido: '{key}'")

    for key, value in answers.items():
        field = fields_by_key.get(key)
        if field is None or value is None:
            continue
        if field.type == FieldType.SELECAO_UNICA:
            if value not in (field.options or []):
                errors.append(f"Campo '{key}': valor '{value}' nao esta entre as opcoes")
        elif field.type == FieldType.SELECAO_MULTIPLA:
            if not isinstance(value, list):
                errors.append(f"Campo '{key}': espera uma lista de opcoes")
            else:
                invalid = [v for v in value if v not in (field.options or [])]
                if invalid:
                    errors.append(f"Campo '{key}': valores invalidos {invalid}")
        elif field.type == FieldType.NUMERO:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"Campo '{key}': deve ser numero")

    return errors


def validate_required_fields(fields: list[FieldDefinition], answers: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in fields:
        if not field.required or not is_field_active(field, answers):
            continue
        value = answers.get(field.key)
        if value is None or value == "" or value == []:
            errors.append(f"Campo obrigatorio nao preenchido: '{field.key}'")
    return errors


def compute_answer_diff(old: dict[str, Any], new: dict[str, Any]) -> list[dict[str, Any]]:
    changes = []
    for key in sorted(set(old) | set(new)):
        old_value = old.get(key)
        new_value = new.get(key)
        if old_value != new_value:
            changes.append({"field": key, "old_value": old_value, "new_value": new_value})
    return changes
