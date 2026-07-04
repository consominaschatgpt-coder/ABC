import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rda_campo/db/app_database.dart';
import 'package:rda_campo/models/field_definition.dart';
import 'package:rda_campo/repositories/rda_repository.dart';

const fields = [
  FieldDefinition(
    key: 'houve_atividade',
    label: 'Houve atividade?',
    type: FieldType.selecaoUnica,
    required: true,
    options: ['sim', 'nao'],
  ),
];

void main() {
  late AppDatabase db;
  late RdaRepository repo;

  setUp(() {
    db = AppDatabase(NativeDatabase.memory());
    repo = RdaRepository(db);
  });

  tearDown(() async {
    await db.close();
  });

  test('createDraft comeca como rascunho local', () async {
    final draft = await repo.createDraft(
      contractId: 'contract-1',
      teamId: 'team-1',
      formTemplateVersionId: 'version-1',
      collectorUserId: 'user-1',
    );
    expect(draft.syncStatus, LocalSyncStatus.rascunhoLocal);
    expect(draft.remoteId, isNull);
  });

  test('updateAnswers persiste as respostas', () async {
    final draft = await repo.createDraft(
      contractId: 'contract-1',
      teamId: 'team-1',
      formTemplateVersionId: 'version-1',
      collectorUserId: 'user-1',
    );
    await repo.updateAnswers(draft.localId, {'houve_atividade': 'sim'});

    final reloaded = await db.localRdaById(draft.localId);
    expect(reloaded.answersJson, contains('sim'));
  });

  test('markReadyToSend falha quando campo obrigatorio esta faltando', () async {
    final draft = await repo.createDraft(
      contractId: 'contract-1',
      teamId: 'team-1',
      formTemplateVersionId: 'version-1',
      collectorUserId: 'user-1',
    );

    expect(() => repo.markReadyToSend(draft.localId, fields), throwsA(isA<ValidationException>()));
  });

  test('markReadyToSend poe o RDA na fila quando valido', () async {
    final draft = await repo.createDraft(
      contractId: 'contract-1',
      teamId: 'team-1',
      formTemplateVersionId: 'version-1',
      collectorUserId: 'user-1',
    );
    await repo.updateAnswers(draft.localId, {'houve_atividade': 'sim'});
    await repo.markReadyToSend(draft.localId, fields);

    final reloaded = await db.localRdaById(draft.localId);
    expect(reloaded.syncStatus, LocalSyncStatus.filaEnvio);
  });

  test('watchForCollector so retorna RDAs do coletor informado', () async {
    await repo.createDraft(
      contractId: 'contract-1',
      teamId: 'team-1',
      formTemplateVersionId: 'version-1',
      collectorUserId: 'user-1',
    );
    await repo.createDraft(
      contractId: 'contract-1',
      teamId: 'team-1',
      formTemplateVersionId: 'version-1',
      collectorUserId: 'user-2',
    );

    final items = await repo.watchForCollector('user-1').first;
    expect(items, hasLength(1));
    expect(items.first.collectorUserId, 'user-1');
  });
}
