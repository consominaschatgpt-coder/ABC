/// Espelha app/schemas/form_template.py (backend) e src/api/types.ts (painel web).
enum FieldType {
  texto,
  numero,
  dataHora,
  selecaoUnica,
  selecaoMultipla,
  foto,
  assinatura,
  localizacao;

  static FieldType fromWire(String value) {
    switch (value) {
      case 'texto':
        return FieldType.texto;
      case 'numero':
        return FieldType.numero;
      case 'data_hora':
        return FieldType.dataHora;
      case 'selecao_unica':
        return FieldType.selecaoUnica;
      case 'selecao_multipla':
        return FieldType.selecaoMultipla;
      case 'foto':
        return FieldType.foto;
      case 'assinatura':
        return FieldType.assinatura;
      case 'localizacao':
        return FieldType.localizacao;
      default:
        throw ArgumentError('Tipo de campo desconhecido: $value');
    }
  }

  String toWire() {
    switch (this) {
      case FieldType.texto:
        return 'texto';
      case FieldType.numero:
        return 'numero';
      case FieldType.dataHora:
        return 'data_hora';
      case FieldType.selecaoUnica:
        return 'selecao_unica';
      case FieldType.selecaoMultipla:
        return 'selecao_multipla';
      case FieldType.foto:
        return 'foto';
      case FieldType.assinatura:
        return 'assinatura';
      case FieldType.localizacao:
        return 'localizacao';
    }
  }
}

const selectionTypes = {FieldType.selecaoUnica, FieldType.selecaoMultipla};

class FieldCondition {
  final String field;
  final String equals;

  const FieldCondition({required this.field, required this.equals});

  factory FieldCondition.fromJson(Map<String, dynamic> json) {
    return FieldCondition(field: json['field'] as String, equals: json['equals'] as String);
  }

  Map<String, dynamic> toJson() => {'field': field, 'equals': equals};
}

class FieldDefinition {
  final String key;
  final String label;
  final FieldType type;
  final bool required;
  final int order;
  final List<String>? options;
  final FieldCondition? condition;

  const FieldDefinition({
    required this.key,
    required this.label,
    required this.type,
    this.required = false,
    this.order = 0,
    this.options,
    this.condition,
  });

  factory FieldDefinition.fromJson(Map<String, dynamic> json) {
    return FieldDefinition(
      key: json['key'] as String,
      label: json['label'] as String,
      type: FieldType.fromWire(json['type'] as String),
      required: json['required'] as bool? ?? false,
      order: json['order'] as int? ?? 0,
      options: (json['options'] as List<dynamic>?)?.map((e) => e as String).toList(),
      condition: json['condition'] != null
          ? FieldCondition.fromJson(json['condition'] as Map<String, dynamic>)
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'key': key,
    'label': label,
    'type': type.toWire(),
    'required': required,
    'order': order,
    'options': options,
    'condition': condition?.toJson(),
  };

  /// Um campo condicional so esta ativo (visivel/obrigatorio) quando a
  /// condicao e satisfeita pelas respostas atuais.
  bool isActive(Map<String, dynamic> answers) {
    if (condition == null) return true;
    return answers[condition!.field]?.toString() == condition!.equals;
  }
}

class FormTemplateVersion {
  final String id;
  final String templateId;
  final int versionNumber;
  final List<FieldDefinition> fields;
  final bool isPublished;

  const FormTemplateVersion({
    required this.id,
    required this.templateId,
    required this.versionNumber,
    required this.fields,
    required this.isPublished,
  });

  factory FormTemplateVersion.fromJson(Map<String, dynamic> json) {
    return FormTemplateVersion(
      id: json['id'] as String,
      templateId: json['template_id'] as String,
      versionNumber: json['version_number'] as int,
      fields: (json['fields'] as List<dynamic>)
          .map((e) => FieldDefinition.fromJson(e as Map<String, dynamic>))
          .toList(),
      isPublished: json['is_published'] as bool,
    );
  }
}
