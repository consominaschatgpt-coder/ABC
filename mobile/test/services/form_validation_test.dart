import 'package:flutter_test/flutter_test.dart';
import 'package:rda_campo/models/field_definition.dart';
import 'package:rda_campo/services/form_validation.dart';

final houveAtividade = FieldDefinition(
  key: 'houve_atividade',
  label: 'Houve atividade?',
  type: FieldType.selecaoUnica,
  required: true,
  options: const ['sim', 'nao'],
);

final tipoSupressao = FieldDefinition(
  key: 'tipo_supressao',
  label: 'Tipo de supressao',
  type: FieldType.selecaoUnica,
  required: true,
  options: const ['Fauna', 'Flora'],
  condition: const FieldCondition(field: 'houve_atividade', equals: 'sim'),
);

const observacoes = FieldDefinition(key: 'observacoes', label: 'Observacoes', type: FieldType.texto);

void main() {
  group('requiredFieldErrors', () {
    test('cobra campo obrigatorio ausente', () {
      final errors = requiredFieldErrors([houveAtividade], {});
      expect(errors, isNotEmpty);
    });

    test('nao cobra campo condicional quando condicao nao satisfeita', () {
      final errors = requiredFieldErrors([houveAtividade, tipoSupressao], {'houve_atividade': 'nao'});
      expect(errors, isEmpty);
    });

    test('cobra campo condicional quando condicao satisfeita', () {
      final errors = requiredFieldErrors([houveAtividade, tipoSupressao], {'houve_atividade': 'sim'});
      expect(errors, contains(contains('Tipo de supressao')));
    });

    test('passa quando tudo preenchido corretamente', () {
      final errors = requiredFieldErrors(
        [houveAtividade, tipoSupressao],
        {'houve_atividade': 'sim', 'tipo_supressao': 'Fauna'},
      );
      expect(errors, isEmpty);
    });

    test('campo nao obrigatorio nunca gera erro', () {
      final errors = requiredFieldErrors([observacoes], {});
      expect(errors, isEmpty);
    });
  });

  group('answerValueErrors', () {
    test('rejeita campo desconhecido', () {
      final errors = answerValueErrors([observacoes], {'campo_fantasma': 'x'});
      expect(errors, contains(contains('desconhecido')));
    });

    test('rejeita valor fora das opcoes em selecao unica', () {
      final errors = answerValueErrors([houveAtividade], {'houve_atividade': 'talvez'});
      expect(errors, isNotEmpty);
    });

    test('aceita valor valido em selecao unica', () {
      final errors = answerValueErrors([houveAtividade], {'houve_atividade': 'sim'});
      expect(errors, isEmpty);
    });

    test('rejeita numero invalido', () {
      const numeroField = FieldDefinition(key: 'idade', label: 'Idade', type: FieldType.numero);
      final errors = answerValueErrors([numeroField], {'idade': 'abc'});
      expect(errors, isNotEmpty);
    });
  });
}
