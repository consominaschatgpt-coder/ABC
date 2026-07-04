import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';

import '../db/app_database.dart';
import '../models/field_definition.dart';
import '../services/form_validation.dart';

class ValidationException implements Exception {
  final List<String> errors;
  ValidationException(this.errors);
}

/// Toda escrita de RDA passa por aqui: cria/edita local (sempre permitido,
/// mesmo offline) e so marca "pronto pra enviar" depois de validar contra o
/// schema do formulario — o SyncEngine so lida com o que ja passou aqui.
class RdaRepository {
  final AppDatabase db;
  final _uuid = const Uuid();

  RdaRepository(this.db);

  Future<LocalRda> createDraft({
    required String contractId,
    required String teamId,
    required String formTemplateVersionId,
    required String collectorUserId,
  }) async {
    final now = DateTime.now();
    final row = LocalRdasCompanion.insert(
      localId: _uuid.v4(),
      contractId: contractId,
      teamId: teamId,
      formTemplateVersionId: formTemplateVersionId,
      collectorUserId: collectorUserId,
      answersJson: jsonEncode(<String, dynamic>{}),
      syncStatus: LocalSyncStatus.rascunhoLocal,
      createdAt: now,
      updatedAt: now,
    );
    await db.into(db.localRdas).insert(row);
    return (db.select(db.localRdas)..where((t) => t.localId.equals(row.localId.value))).getSingle();
  }

  Future<void> updateAnswers(String localId, Map<String, dynamic> answers) async {
    await (db.update(db.localRdas)..where((t) => t.localId.equals(localId))).write(
      LocalRdasCompanion(answersJson: Value(jsonEncode(answers)), updatedAt: Value(DateTime.now())),
    );
  }

  /// Valida os campos obrigatorios (respeitando condicoes) e, se ok, poe o
  /// RDA na fila de sincronizacao. Espelha o POST /rdas/{id}/submit do
  /// backend, mas roda 100% local.
  Future<void> markReadyToSend(String localId, List<FieldDefinition> fields) async {
    final rda = await (db.select(db.localRdas)..where((t) => t.localId.equals(localId))).getSingle();
    final answers = jsonDecode(rda.answersJson) as Map<String, dynamic>;

    final errors = [...answerValueErrors(fields, answers), ...requiredFieldErrors(fields, answers)];
    if (errors.isNotEmpty) throw ValidationException(errors);

    await (db.update(db.localRdas)..where((t) => t.localId.equals(localId))).write(
      LocalRdasCompanion(
        syncStatus: const Value(LocalSyncStatus.filaEnvio),
        syncError: const Value(null),
        updatedAt: Value(DateTime.now()),
      ),
    );
  }

  Stream<List<LocalRda>> watchForCollector(String collectorUserId) =>
      db.watchRdasForCollector(collectorUserId);
}
