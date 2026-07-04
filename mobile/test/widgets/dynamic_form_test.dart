import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rda_campo/models/field_definition.dart';
import 'package:rda_campo/widgets/dynamic_form.dart';

const houveAtividade = FieldDefinition(
  key: 'houve_atividade',
  label: 'Houve atividade?',
  type: FieldType.selecaoUnica,
  required: true,
  options: ['sim', 'nao'],
);

const tipoSupressao = FieldDefinition(
  key: 'tipo_supressao',
  label: 'Tipo de supressao',
  type: FieldType.selecaoUnica,
  options: ['Fauna', 'Flora'],
  condition: FieldCondition(field: 'houve_atividade', equals: 'sim'),
);

const observacoes = FieldDefinition(key: 'observacoes', label: 'Observacoes', type: FieldType.texto);

Widget wrap(Widget child) => MaterialApp(home: Scaffold(body: SingleChildScrollView(child: child)));

void main() {
  testWidgets('campo condicional so aparece quando a condicao e satisfeita', (tester) async {
    Map<String, dynamic>? lastAnswers;
    await tester.pumpWidget(
      wrap(
        DynamicForm(
          fields: const [houveAtividade, tipoSupressao],
          initialAnswers: const {},
          onChanged: (answers) => lastAnswers = answers,
        ),
      ),
    );

    expect(find.text('Tipo de supressao'), findsNothing);

    await tester.tap(find.byKey(const Key('field_houve_atividade')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('sim').last);
    await tester.pumpAndSettle();

    expect(find.text('Tipo de supressao'), findsOneWidget);
    expect(lastAnswers, {'houve_atividade': 'sim'});
  });

  testWidgets('texto livre atualiza as respostas', (tester) async {
    Map<String, dynamic>? lastAnswers;
    await tester.pumpWidget(
      wrap(
        DynamicForm(
          fields: const [observacoes],
          initialAnswers: const {},
          onChanged: (answers) => lastAnswers = answers,
        ),
      ),
    );

    await tester.enterText(find.byKey(const Key('field_observacoes')), 'tudo certo no talhao');
    expect(lastAnswers, {'observacoes': 'tudo certo no talhao'});
  });

  testWidgets('selecao multipla acumula opcoes marcadas', (tester) async {
    const multi = FieldDefinition(
      key: 'especies',
      label: 'Especies',
      type: FieldType.selecaoMultipla,
      options: ['Fauna', 'Flora', 'Biota aquatica'],
    );
    Map<String, dynamic>? lastAnswers;
    await tester.pumpWidget(
      wrap(
        DynamicForm(
          fields: const [multi],
          initialAnswers: const {},
          onChanged: (answers) => lastAnswers = answers,
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('option_Fauna')));
    await tester.pump();
    await tester.tap(find.byKey(const Key('option_Flora')));
    await tester.pump();

    expect(lastAnswers?['especies'], containsAll(['Fauna', 'Flora']));
  });

  testWidgets('readOnly desabilita edicao', (tester) async {
    await tester.pumpWidget(
      wrap(
        DynamicForm(
          fields: const [observacoes],
          initialAnswers: const {'observacoes': 'valor fixo'},
          onChanged: (_) {},
          readOnly: true,
        ),
      ),
    );

    final field = tester.widget<TextFormField>(find.byKey(const Key('field_observacoes')));
    expect(field.enabled, isFalse);
  });
}
