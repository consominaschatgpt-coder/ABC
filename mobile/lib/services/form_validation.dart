import '../models/field_definition.dart';

/// Espelha app/services/form_validation.py (backend): precisa rodar
/// localmente porque o coletor esta offline no momento de preencher e
/// enviar o RDA — nao da pra esperar o servidor validar.
List<String> requiredFieldErrors(List<FieldDefinition> fields, Map<String, dynamic> answers) {
  final errors = <String>[];
  for (final field in fields) {
    if (!field.required || !field.isActive(answers)) continue;
    final value = answers[field.key];
    final isEmpty =
        value == null ||
        (value is String && value.isEmpty) ||
        (value is List && value.isEmpty);
    if (isEmpty) {
      errors.add("Campo obrigatorio nao preenchido: '${field.label}'");
    }
  }
  return errors;
}

List<String> answerValueErrors(List<FieldDefinition> fields, Map<String, dynamic> answers) {
  final errors = <String>[];
  final byKey = {for (final f in fields) f.key: f};

  for (final key in answers.keys) {
    if (!byKey.containsKey(key)) {
      errors.add("Campo desconhecido: '$key'");
    }
  }

  for (final entry in answers.entries) {
    final field = byKey[entry.key];
    final value = entry.value;
    if (field == null || value == null) continue;

    if (field.type == FieldType.selecaoUnica) {
      if (!(field.options ?? const []).contains(value)) {
        errors.add("Campo '${field.key}': valor '$value' nao esta entre as opcoes");
      }
    } else if (field.type == FieldType.selecaoMultipla) {
      if (value is! List) {
        errors.add("Campo '${field.key}': espera uma lista de opcoes");
      } else {
        final invalid = value.where((v) => !(field.options ?? const []).contains(v)).toList();
        if (invalid.isNotEmpty) {
          errors.add("Campo '${field.key}': valores invalidos $invalid");
        }
      }
    } else if (field.type == FieldType.numero) {
      if (value is! num) {
        errors.add("Campo '${field.key}': deve ser numero");
      }
    }
  }

  return errors;
}
