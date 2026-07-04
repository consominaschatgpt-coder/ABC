import 'dart:convert';

import '../core/api_client.dart';
import '../db/app_database.dart';
import '../models/field_definition.dart';

/// Mantem uma copia local do formulario publicado de cada contrato, para o
/// coletor conseguir montar um novo RDA mesmo sem sinal (desde que o app
/// tenha sincronizado uma vez online).
class FormTemplateRepository {
  final ApiClient api;
  final AppDatabase db;

  FormTemplateRepository({required this.api, required this.db});

  Future<void> refreshForContract(String contractId) async {
    final templates = await api.get('/form-templates', query: {'contract_id': contractId}) as List;
    if (templates.isEmpty) return;

    final templateId = templates.first['id'] as String;
    final detail = await api.get('/form-templates/$templateId') as Map<String, dynamic>;
    final currentVersion = detail['current_version'] as Map<String, dynamic>?;
    if (currentVersion == null) return;

    await db
        .into(db.cachedFormVersions)
        .insertOnConflictUpdate(
          CachedFormVersionsCompanion.insert(
            id: currentVersion['id'] as String,
            templateId: templateId,
            contractId: contractId,
            versionNumber: currentVersion['version_number'] as int,
            fieldsJson: jsonEncode(currentVersion['fields']),
            cachedAt: DateTime.now(),
          ),
        );
  }

  Future<List<FieldDefinition>?> fieldsForContract(String contractId) async {
    final cached = await db.currentFormForContract(contractId);
    if (cached == null) return null;
    return _decodeFields(cached.fieldsJson);
  }

  Future<String?> formVersionIdForContract(String contractId) async {
    final cached = await db.currentFormForContract(contractId);
    return cached?.id;
  }

  /// Um LocalRda ja aponta pra uma versao especifica (imutavel) do
  /// formulario — precisa renderizar exatamente essa versao, mesmo que o
  /// cache do contrato ja tenha avancado para uma versao mais nova.
  Future<List<FieldDefinition>> fieldsForVersionId(String versionId) async {
    final cached = await db.cachedFormById(versionId);
    if (cached == null) {
      throw StateError('Formulario $versionId nao esta em cache local');
    }
    return _decodeFields(cached.fieldsJson);
  }

  List<FieldDefinition> _decodeFields(String fieldsJson) {
    final list = jsonDecode(fieldsJson) as List<dynamic>;
    return list.map((e) => FieldDefinition.fromJson(e as Map<String, dynamic>)).toList();
  }
}
