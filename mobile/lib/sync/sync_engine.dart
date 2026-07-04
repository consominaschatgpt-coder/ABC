import 'dart:async';
import 'dart:convert';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:drift/drift.dart';

import '../core/api_client.dart';
import '../db/app_database.dart';

/// Fila de sincronizacao: observa conectividade e, ao voltar o sinal,
/// envia os RDAs marcados como "fila de envio" (ou "erro", para retry).
/// Cada RDA vira uma dupla de chamadas no backend: POST /rdas (cria) e
/// POST /rdas/{id}/submit (envia) — refletindo a maquina de estados do
/// servidor (rascunho -> enviado).
class SyncEngine {
  final AppDatabase db;
  final ApiClient api;
  final Connectivity connectivity;

  StreamSubscription<List<ConnectivityResult>>? _subscription;
  bool _syncing = false;

  final _statusController = StreamController<String>.broadcast();
  Stream<String> get statusMessages => _statusController.stream;

  SyncEngine({required this.db, required this.api, Connectivity? connectivity})
    : connectivity = connectivity ?? Connectivity();

  void start() {
    _subscription = connectivity.onConnectivityChanged.listen((results) {
      if (!results.contains(ConnectivityResult.none)) {
        syncNow();
      }
    });
  }

  void dispose() {
    _subscription?.cancel();
    _statusController.close();
  }

  Future<void> syncNow() async {
    if (_syncing) return;
    _syncing = true;
    try {
      final pending = await db.pendingSyncItems();
      for (final item in pending) {
        await _syncOne(item);
      }
    } finally {
      _syncing = false;
    }
  }

  Future<void> _syncOne(LocalRda item) async {
    await (db.update(db.localRdas)..where((t) => t.localId.equals(item.localId))).write(
      const LocalRdasCompanion(syncStatus: Value(LocalSyncStatus.enviando)),
    );

    try {
      var remoteId = item.remoteId;
      if (remoteId == null) {
        final answers = jsonDecode(item.answersJson) as Map<String, dynamic>;
        final created = await api.post(
          '/rdas',
          body: {
            'contract_id': item.contractId,
            'team_id': item.teamId,
            'form_template_version_id': item.formTemplateVersionId,
            'answers': answers,
          },
        );
        remoteId = created['id'] as String;
      }

      await api.post('/rdas/$remoteId/submit');

      await (db.update(db.localRdas)..where((t) => t.localId.equals(item.localId))).write(
        LocalRdasCompanion(
          remoteId: Value(remoteId),
          syncStatus: const Value(LocalSyncStatus.sincronizado),
          syncError: const Value(null),
          updatedAt: Value(DateTime.now()),
        ),
      );
      _statusController.add('RDA ${item.localId} sincronizado');
    } catch (err) {
      await (db.update(db.localRdas)..where((t) => t.localId.equals(item.localId))).write(
        LocalRdasCompanion(
          syncStatus: const Value(LocalSyncStatus.erro),
          syncError: Value(err.toString()),
          updatedAt: Value(DateTime.now()),
        ),
      );
      _statusController.add('Falha ao sincronizar ${item.localId}: $err');
    }
  }
}
