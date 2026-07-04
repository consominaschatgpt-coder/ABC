import 'dart:convert';

import 'package:drift/drift.dart' hide isNotNull;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:rda_campo/core/api_client.dart';
import 'package:rda_campo/db/app_database.dart';
import 'package:rda_campo/repositories/rda_repository.dart';
import 'package:rda_campo/sync/sync_engine.dart';

void main() {
  late AppDatabase db;
  late RdaRepository rdaRepo;

  setUp(() {
    db = AppDatabase(NativeDatabase.memory());
    rdaRepo = RdaRepository(db);
  });

  tearDown(() async {
    await db.close();
  });

  test('sincroniza um RDA na fila: cria e envia no backend', () async {
    final requests = <String>[];
    final mockClient = MockClient((request) async {
      requests.add('${request.method} ${request.url.path}');
      if (request.method == 'POST' && request.url.path == '/rdas') {
        return http.Response(
          jsonEncode({'id': 'remote-123'}),
          201,
          headers: {'content-type': 'application/json'},
        );
      }
      if (request.method == 'POST' && request.url.path == '/rdas/remote-123/submit') {
        return http.Response(
          jsonEncode({'id': 'remote-123', 'status': 'enviado'}),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      return http.Response('not found', 404);
    });

    final api = ApiClient(baseUrl: 'http://test', client: mockClient);
    final engine = SyncEngine(db: db, api: api);

    final draft = await rdaRepo.createDraft(
      contractId: 'contract-1',
      teamId: 'team-1',
      formTemplateVersionId: 'version-1',
      collectorUserId: 'user-1',
    );
    await rdaRepo.updateAnswers(draft.localId, {'houve_atividade': 'sim'});
    await db
        .update(db.localRdas)
        .replace(draft.copyWith(syncStatus: LocalSyncStatus.filaEnvio));

    await engine.syncNow();

    final reloaded = await db.localRdaById(draft.localId);
    expect(reloaded.syncStatus, LocalSyncStatus.sincronizado);
    expect(reloaded.remoteId, 'remote-123');
    expect(requests, ['POST /rdas', 'POST /rdas/remote-123/submit']);
  });

  test('marca erro e mantem na fila quando o backend falha', () async {
    final mockClient = MockClient((request) async => http.Response('erro interno', 500));
    final api = ApiClient(baseUrl: 'http://test', client: mockClient);
    final engine = SyncEngine(db: db, api: api);

    final draft = await rdaRepo.createDraft(
      contractId: 'contract-1',
      teamId: 'team-1',
      formTemplateVersionId: 'version-1',
      collectorUserId: 'user-1',
    );
    await db
        .update(db.localRdas)
        .replace(draft.copyWith(syncStatus: LocalSyncStatus.filaEnvio));

    await engine.syncNow();

    final reloaded = await db.localRdaById(draft.localId);
    expect(reloaded.syncStatus, LocalSyncStatus.erro);
    expect(reloaded.syncError, isNotNull);
  });

  test('retry reaproveita o remoteId ja criado (nao duplica o RDA)', () async {
    final requests = <String>[];
    final mockClient = MockClient((request) async {
      requests.add('${request.method} ${request.url.path}');
      return http.Response(
        jsonEncode({'id': 'remote-999', 'status': 'enviado'}),
        200,
        headers: {'content-type': 'application/json'},
      );
    });
    final api = ApiClient(baseUrl: 'http://test', client: mockClient);
    final engine = SyncEngine(db: db, api: api);

    final draft = await rdaRepo.createDraft(
      contractId: 'contract-1',
      teamId: 'team-1',
      formTemplateVersionId: 'version-1',
      collectorUserId: 'user-1',
    );
    await db
        .update(db.localRdas)
        .replace(draft.copyWith(syncStatus: LocalSyncStatus.erro, remoteId: const Value('remote-999')));

    await engine.syncNow();

    expect(requests, ['POST /rdas/remote-999/submit']);
  });
}
