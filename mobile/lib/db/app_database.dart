import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

part 'app_database.g.dart';

/// Cache local do formulario publicado de um contrato — permite montar um
/// novo RDA mesmo sem conexao, desde que o app tenha sincronizado uma vez
/// com sinal.
class CachedFormVersions extends Table {
  TextColumn get id => text()(); // form_template_version_id do backend
  TextColumn get templateId => text()();
  TextColumn get contractId => text()();
  IntColumn get versionNumber => integer()();
  TextColumn get fieldsJson => text()(); // List<FieldDefinition> serializado
  DateTimeColumn get cachedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

/// Status de sincronizacao local. Nao confundir com o status de negocio do
/// RDA no backend (rascunho/enviado/em_revisao/...) — aqui e so "esse
/// registro local ja foi enviado pro servidor ou ainda esta na fila".
enum LocalSyncStatus { rascunhoLocal, filaEnvio, enviando, sincronizado, erro }

class LocalRdas extends Table {
  TextColumn get localId => text()(); // uuid gerado no aparelho
  TextColumn get remoteId => text().nullable()(); // id do RDA no backend, apos 1o sync
  TextColumn get contractId => text()();
  TextColumn get teamId => text()();
  TextColumn get formTemplateVersionId => text()();
  TextColumn get collectorUserId => text()();
  TextColumn get answersJson => text()();
  TextColumn get syncStatus => textEnum<LocalSyncStatus>()();
  TextColumn get syncError => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {localId};
}

@DriftDatabase(tables: [CachedFormVersions, LocalRdas])
class AppDatabase extends _$AppDatabase {
  AppDatabase([QueryExecutor? executor]) : super(executor ?? _openConnection());

  @override
  int get schemaVersion => 1;

  static QueryExecutor _openConnection() {
    return LazyDatabase(() async {
      final dir = await getApplicationDocumentsDirectory();
      final file = File(p.join(dir.path, 'rda_campo.sqlite'));
      return NativeDatabase.createInBackground(file);
    });
  }

  Future<List<LocalRda>> pendingSyncItems() {
    return (select(localRdas)..where(
          (t) =>
              t.syncStatus.equalsValue(LocalSyncStatus.filaEnvio) |
              t.syncStatus.equalsValue(LocalSyncStatus.erro),
        ))
        .get();
  }

  Stream<List<LocalRda>> watchRdasForCollector(String collectorUserId) {
    return (select(localRdas)
          ..where((t) => t.collectorUserId.equals(collectorUserId))
          ..orderBy([(t) => OrderingTerm.desc(t.createdAt)]))
        .watch();
  }

  Future<CachedFormVersion?> currentFormForContract(String contractId) async {
    final query = select(cachedFormVersions)
      ..where((t) => t.contractId.equals(contractId))
      ..orderBy([(t) => OrderingTerm.desc(t.versionNumber)])
      ..limit(1);
    return query.getSingleOrNull();
  }

  Future<CachedFormVersion?> cachedFormById(String id) {
    return (select(cachedFormVersions)..where((t) => t.id.equals(id))).getSingleOrNull();
  }

  Future<LocalRda> localRdaById(String localId) {
    return (select(localRdas)..where((t) => t.localId.equals(localId))).getSingle();
  }

  Stream<LocalRda> watchLocalRda(String localId) {
    return (select(localRdas)..where((t) => t.localId.equals(localId))).watchSingle();
  }
}
