// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $CachedFormVersionsTable extends CachedFormVersions
    with TableInfo<$CachedFormVersionsTable, CachedFormVersion> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedFormVersionsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _templateIdMeta = const VerificationMeta(
    'templateId',
  );
  @override
  late final GeneratedColumn<String> templateId = GeneratedColumn<String>(
    'template_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _contractIdMeta = const VerificationMeta(
    'contractId',
  );
  @override
  late final GeneratedColumn<String> contractId = GeneratedColumn<String>(
    'contract_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _versionNumberMeta = const VerificationMeta(
    'versionNumber',
  );
  @override
  late final GeneratedColumn<int> versionNumber = GeneratedColumn<int>(
    'version_number',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _fieldsJsonMeta = const VerificationMeta(
    'fieldsJson',
  );
  @override
  late final GeneratedColumn<String> fieldsJson = GeneratedColumn<String>(
    'fields_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _cachedAtMeta = const VerificationMeta(
    'cachedAt',
  );
  @override
  late final GeneratedColumn<DateTime> cachedAt = GeneratedColumn<DateTime>(
    'cached_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    templateId,
    contractId,
    versionNumber,
    fieldsJson,
    cachedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_form_versions';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedFormVersion> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('template_id')) {
      context.handle(
        _templateIdMeta,
        templateId.isAcceptableOrUnknown(data['template_id']!, _templateIdMeta),
      );
    } else if (isInserting) {
      context.missing(_templateIdMeta);
    }
    if (data.containsKey('contract_id')) {
      context.handle(
        _contractIdMeta,
        contractId.isAcceptableOrUnknown(data['contract_id']!, _contractIdMeta),
      );
    } else if (isInserting) {
      context.missing(_contractIdMeta);
    }
    if (data.containsKey('version_number')) {
      context.handle(
        _versionNumberMeta,
        versionNumber.isAcceptableOrUnknown(
          data['version_number']!,
          _versionNumberMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_versionNumberMeta);
    }
    if (data.containsKey('fields_json')) {
      context.handle(
        _fieldsJsonMeta,
        fieldsJson.isAcceptableOrUnknown(data['fields_json']!, _fieldsJsonMeta),
      );
    } else if (isInserting) {
      context.missing(_fieldsJsonMeta);
    }
    if (data.containsKey('cached_at')) {
      context.handle(
        _cachedAtMeta,
        cachedAt.isAcceptableOrUnknown(data['cached_at']!, _cachedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_cachedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedFormVersion map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedFormVersion(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      templateId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}template_id'],
      )!,
      contractId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}contract_id'],
      )!,
      versionNumber: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}version_number'],
      )!,
      fieldsJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}fields_json'],
      )!,
      cachedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}cached_at'],
      )!,
    );
  }

  @override
  $CachedFormVersionsTable createAlias(String alias) {
    return $CachedFormVersionsTable(attachedDatabase, alias);
  }
}

class CachedFormVersion extends DataClass
    implements Insertable<CachedFormVersion> {
  final String id;
  final String templateId;
  final String contractId;
  final int versionNumber;
  final String fieldsJson;
  final DateTime cachedAt;
  const CachedFormVersion({
    required this.id,
    required this.templateId,
    required this.contractId,
    required this.versionNumber,
    required this.fieldsJson,
    required this.cachedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['template_id'] = Variable<String>(templateId);
    map['contract_id'] = Variable<String>(contractId);
    map['version_number'] = Variable<int>(versionNumber);
    map['fields_json'] = Variable<String>(fieldsJson);
    map['cached_at'] = Variable<DateTime>(cachedAt);
    return map;
  }

  CachedFormVersionsCompanion toCompanion(bool nullToAbsent) {
    return CachedFormVersionsCompanion(
      id: Value(id),
      templateId: Value(templateId),
      contractId: Value(contractId),
      versionNumber: Value(versionNumber),
      fieldsJson: Value(fieldsJson),
      cachedAt: Value(cachedAt),
    );
  }

  factory CachedFormVersion.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedFormVersion(
      id: serializer.fromJson<String>(json['id']),
      templateId: serializer.fromJson<String>(json['templateId']),
      contractId: serializer.fromJson<String>(json['contractId']),
      versionNumber: serializer.fromJson<int>(json['versionNumber']),
      fieldsJson: serializer.fromJson<String>(json['fieldsJson']),
      cachedAt: serializer.fromJson<DateTime>(json['cachedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'templateId': serializer.toJson<String>(templateId),
      'contractId': serializer.toJson<String>(contractId),
      'versionNumber': serializer.toJson<int>(versionNumber),
      'fieldsJson': serializer.toJson<String>(fieldsJson),
      'cachedAt': serializer.toJson<DateTime>(cachedAt),
    };
  }

  CachedFormVersion copyWith({
    String? id,
    String? templateId,
    String? contractId,
    int? versionNumber,
    String? fieldsJson,
    DateTime? cachedAt,
  }) => CachedFormVersion(
    id: id ?? this.id,
    templateId: templateId ?? this.templateId,
    contractId: contractId ?? this.contractId,
    versionNumber: versionNumber ?? this.versionNumber,
    fieldsJson: fieldsJson ?? this.fieldsJson,
    cachedAt: cachedAt ?? this.cachedAt,
  );
  CachedFormVersion copyWithCompanion(CachedFormVersionsCompanion data) {
    return CachedFormVersion(
      id: data.id.present ? data.id.value : this.id,
      templateId: data.templateId.present
          ? data.templateId.value
          : this.templateId,
      contractId: data.contractId.present
          ? data.contractId.value
          : this.contractId,
      versionNumber: data.versionNumber.present
          ? data.versionNumber.value
          : this.versionNumber,
      fieldsJson: data.fieldsJson.present
          ? data.fieldsJson.value
          : this.fieldsJson,
      cachedAt: data.cachedAt.present ? data.cachedAt.value : this.cachedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedFormVersion(')
          ..write('id: $id, ')
          ..write('templateId: $templateId, ')
          ..write('contractId: $contractId, ')
          ..write('versionNumber: $versionNumber, ')
          ..write('fieldsJson: $fieldsJson, ')
          ..write('cachedAt: $cachedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    templateId,
    contractId,
    versionNumber,
    fieldsJson,
    cachedAt,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedFormVersion &&
          other.id == this.id &&
          other.templateId == this.templateId &&
          other.contractId == this.contractId &&
          other.versionNumber == this.versionNumber &&
          other.fieldsJson == this.fieldsJson &&
          other.cachedAt == this.cachedAt);
}

class CachedFormVersionsCompanion extends UpdateCompanion<CachedFormVersion> {
  final Value<String> id;
  final Value<String> templateId;
  final Value<String> contractId;
  final Value<int> versionNumber;
  final Value<String> fieldsJson;
  final Value<DateTime> cachedAt;
  final Value<int> rowid;
  const CachedFormVersionsCompanion({
    this.id = const Value.absent(),
    this.templateId = const Value.absent(),
    this.contractId = const Value.absent(),
    this.versionNumber = const Value.absent(),
    this.fieldsJson = const Value.absent(),
    this.cachedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedFormVersionsCompanion.insert({
    required String id,
    required String templateId,
    required String contractId,
    required int versionNumber,
    required String fieldsJson,
    required DateTime cachedAt,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       templateId = Value(templateId),
       contractId = Value(contractId),
       versionNumber = Value(versionNumber),
       fieldsJson = Value(fieldsJson),
       cachedAt = Value(cachedAt);
  static Insertable<CachedFormVersion> custom({
    Expression<String>? id,
    Expression<String>? templateId,
    Expression<String>? contractId,
    Expression<int>? versionNumber,
    Expression<String>? fieldsJson,
    Expression<DateTime>? cachedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (templateId != null) 'template_id': templateId,
      if (contractId != null) 'contract_id': contractId,
      if (versionNumber != null) 'version_number': versionNumber,
      if (fieldsJson != null) 'fields_json': fieldsJson,
      if (cachedAt != null) 'cached_at': cachedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedFormVersionsCompanion copyWith({
    Value<String>? id,
    Value<String>? templateId,
    Value<String>? contractId,
    Value<int>? versionNumber,
    Value<String>? fieldsJson,
    Value<DateTime>? cachedAt,
    Value<int>? rowid,
  }) {
    return CachedFormVersionsCompanion(
      id: id ?? this.id,
      templateId: templateId ?? this.templateId,
      contractId: contractId ?? this.contractId,
      versionNumber: versionNumber ?? this.versionNumber,
      fieldsJson: fieldsJson ?? this.fieldsJson,
      cachedAt: cachedAt ?? this.cachedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (templateId.present) {
      map['template_id'] = Variable<String>(templateId.value);
    }
    if (contractId.present) {
      map['contract_id'] = Variable<String>(contractId.value);
    }
    if (versionNumber.present) {
      map['version_number'] = Variable<int>(versionNumber.value);
    }
    if (fieldsJson.present) {
      map['fields_json'] = Variable<String>(fieldsJson.value);
    }
    if (cachedAt.present) {
      map['cached_at'] = Variable<DateTime>(cachedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedFormVersionsCompanion(')
          ..write('id: $id, ')
          ..write('templateId: $templateId, ')
          ..write('contractId: $contractId, ')
          ..write('versionNumber: $versionNumber, ')
          ..write('fieldsJson: $fieldsJson, ')
          ..write('cachedAt: $cachedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $LocalRdasTable extends LocalRdas
    with TableInfo<$LocalRdasTable, LocalRda> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalRdasTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _localIdMeta = const VerificationMeta(
    'localId',
  );
  @override
  late final GeneratedColumn<String> localId = GeneratedColumn<String>(
    'local_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _remoteIdMeta = const VerificationMeta(
    'remoteId',
  );
  @override
  late final GeneratedColumn<String> remoteId = GeneratedColumn<String>(
    'remote_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _contractIdMeta = const VerificationMeta(
    'contractId',
  );
  @override
  late final GeneratedColumn<String> contractId = GeneratedColumn<String>(
    'contract_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _teamIdMeta = const VerificationMeta('teamId');
  @override
  late final GeneratedColumn<String> teamId = GeneratedColumn<String>(
    'team_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _formTemplateVersionIdMeta =
      const VerificationMeta('formTemplateVersionId');
  @override
  late final GeneratedColumn<String> formTemplateVersionId =
      GeneratedColumn<String>(
        'form_template_version_id',
        aliasedName,
        false,
        type: DriftSqlType.string,
        requiredDuringInsert: true,
      );
  static const VerificationMeta _collectorUserIdMeta = const VerificationMeta(
    'collectorUserId',
  );
  @override
  late final GeneratedColumn<String> collectorUserId = GeneratedColumn<String>(
    'collector_user_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _answersJsonMeta = const VerificationMeta(
    'answersJson',
  );
  @override
  late final GeneratedColumn<String> answersJson = GeneratedColumn<String>(
    'answers_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  late final GeneratedColumnWithTypeConverter<LocalSyncStatus, String>
  syncStatus = GeneratedColumn<String>(
    'sync_status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  ).withConverter<LocalSyncStatus>($LocalRdasTable.$convertersyncStatus);
  static const VerificationMeta _syncErrorMeta = const VerificationMeta(
    'syncError',
  );
  @override
  late final GeneratedColumn<String> syncError = GeneratedColumn<String>(
    'sync_error',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<DateTime> updatedAt = GeneratedColumn<DateTime>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    localId,
    remoteId,
    contractId,
    teamId,
    formTemplateVersionId,
    collectorUserId,
    answersJson,
    syncStatus,
    syncError,
    createdAt,
    updatedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_rdas';
  @override
  VerificationContext validateIntegrity(
    Insertable<LocalRda> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('local_id')) {
      context.handle(
        _localIdMeta,
        localId.isAcceptableOrUnknown(data['local_id']!, _localIdMeta),
      );
    } else if (isInserting) {
      context.missing(_localIdMeta);
    }
    if (data.containsKey('remote_id')) {
      context.handle(
        _remoteIdMeta,
        remoteId.isAcceptableOrUnknown(data['remote_id']!, _remoteIdMeta),
      );
    }
    if (data.containsKey('contract_id')) {
      context.handle(
        _contractIdMeta,
        contractId.isAcceptableOrUnknown(data['contract_id']!, _contractIdMeta),
      );
    } else if (isInserting) {
      context.missing(_contractIdMeta);
    }
    if (data.containsKey('team_id')) {
      context.handle(
        _teamIdMeta,
        teamId.isAcceptableOrUnknown(data['team_id']!, _teamIdMeta),
      );
    } else if (isInserting) {
      context.missing(_teamIdMeta);
    }
    if (data.containsKey('form_template_version_id')) {
      context.handle(
        _formTemplateVersionIdMeta,
        formTemplateVersionId.isAcceptableOrUnknown(
          data['form_template_version_id']!,
          _formTemplateVersionIdMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_formTemplateVersionIdMeta);
    }
    if (data.containsKey('collector_user_id')) {
      context.handle(
        _collectorUserIdMeta,
        collectorUserId.isAcceptableOrUnknown(
          data['collector_user_id']!,
          _collectorUserIdMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_collectorUserIdMeta);
    }
    if (data.containsKey('answers_json')) {
      context.handle(
        _answersJsonMeta,
        answersJson.isAcceptableOrUnknown(
          data['answers_json']!,
          _answersJsonMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_answersJsonMeta);
    }
    if (data.containsKey('sync_error')) {
      context.handle(
        _syncErrorMeta,
        syncError.isAcceptableOrUnknown(data['sync_error']!, _syncErrorMeta),
      );
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {localId};
  @override
  LocalRda map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalRda(
      localId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}local_id'],
      )!,
      remoteId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}remote_id'],
      ),
      contractId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}contract_id'],
      )!,
      teamId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}team_id'],
      )!,
      formTemplateVersionId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}form_template_version_id'],
      )!,
      collectorUserId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}collector_user_id'],
      )!,
      answersJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}answers_json'],
      )!,
      syncStatus: $LocalRdasTable.$convertersyncStatus.fromSql(
        attachedDatabase.typeMapping.read(
          DriftSqlType.string,
          data['${effectivePrefix}sync_status'],
        )!,
      ),
      syncError: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_error'],
      ),
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      )!,
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}updated_at'],
      )!,
    );
  }

  @override
  $LocalRdasTable createAlias(String alias) {
    return $LocalRdasTable(attachedDatabase, alias);
  }

  static JsonTypeConverter2<LocalSyncStatus, String, String>
  $convertersyncStatus = const EnumNameConverter<LocalSyncStatus>(
    LocalSyncStatus.values,
  );
}

class LocalRda extends DataClass implements Insertable<LocalRda> {
  final String localId;
  final String? remoteId;
  final String contractId;
  final String teamId;
  final String formTemplateVersionId;
  final String collectorUserId;
  final String answersJson;
  final LocalSyncStatus syncStatus;
  final String? syncError;
  final DateTime createdAt;
  final DateTime updatedAt;
  const LocalRda({
    required this.localId,
    this.remoteId,
    required this.contractId,
    required this.teamId,
    required this.formTemplateVersionId,
    required this.collectorUserId,
    required this.answersJson,
    required this.syncStatus,
    this.syncError,
    required this.createdAt,
    required this.updatedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['local_id'] = Variable<String>(localId);
    if (!nullToAbsent || remoteId != null) {
      map['remote_id'] = Variable<String>(remoteId);
    }
    map['contract_id'] = Variable<String>(contractId);
    map['team_id'] = Variable<String>(teamId);
    map['form_template_version_id'] = Variable<String>(formTemplateVersionId);
    map['collector_user_id'] = Variable<String>(collectorUserId);
    map['answers_json'] = Variable<String>(answersJson);
    {
      map['sync_status'] = Variable<String>(
        $LocalRdasTable.$convertersyncStatus.toSql(syncStatus),
      );
    }
    if (!nullToAbsent || syncError != null) {
      map['sync_error'] = Variable<String>(syncError);
    }
    map['created_at'] = Variable<DateTime>(createdAt);
    map['updated_at'] = Variable<DateTime>(updatedAt);
    return map;
  }

  LocalRdasCompanion toCompanion(bool nullToAbsent) {
    return LocalRdasCompanion(
      localId: Value(localId),
      remoteId: remoteId == null && nullToAbsent
          ? const Value.absent()
          : Value(remoteId),
      contractId: Value(contractId),
      teamId: Value(teamId),
      formTemplateVersionId: Value(formTemplateVersionId),
      collectorUserId: Value(collectorUserId),
      answersJson: Value(answersJson),
      syncStatus: Value(syncStatus),
      syncError: syncError == null && nullToAbsent
          ? const Value.absent()
          : Value(syncError),
      createdAt: Value(createdAt),
      updatedAt: Value(updatedAt),
    );
  }

  factory LocalRda.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalRda(
      localId: serializer.fromJson<String>(json['localId']),
      remoteId: serializer.fromJson<String?>(json['remoteId']),
      contractId: serializer.fromJson<String>(json['contractId']),
      teamId: serializer.fromJson<String>(json['teamId']),
      formTemplateVersionId: serializer.fromJson<String>(
        json['formTemplateVersionId'],
      ),
      collectorUserId: serializer.fromJson<String>(json['collectorUserId']),
      answersJson: serializer.fromJson<String>(json['answersJson']),
      syncStatus: $LocalRdasTable.$convertersyncStatus.fromJson(
        serializer.fromJson<String>(json['syncStatus']),
      ),
      syncError: serializer.fromJson<String?>(json['syncError']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      updatedAt: serializer.fromJson<DateTime>(json['updatedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'localId': serializer.toJson<String>(localId),
      'remoteId': serializer.toJson<String?>(remoteId),
      'contractId': serializer.toJson<String>(contractId),
      'teamId': serializer.toJson<String>(teamId),
      'formTemplateVersionId': serializer.toJson<String>(formTemplateVersionId),
      'collectorUserId': serializer.toJson<String>(collectorUserId),
      'answersJson': serializer.toJson<String>(answersJson),
      'syncStatus': serializer.toJson<String>(
        $LocalRdasTable.$convertersyncStatus.toJson(syncStatus),
      ),
      'syncError': serializer.toJson<String?>(syncError),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'updatedAt': serializer.toJson<DateTime>(updatedAt),
    };
  }

  LocalRda copyWith({
    String? localId,
    Value<String?> remoteId = const Value.absent(),
    String? contractId,
    String? teamId,
    String? formTemplateVersionId,
    String? collectorUserId,
    String? answersJson,
    LocalSyncStatus? syncStatus,
    Value<String?> syncError = const Value.absent(),
    DateTime? createdAt,
    DateTime? updatedAt,
  }) => LocalRda(
    localId: localId ?? this.localId,
    remoteId: remoteId.present ? remoteId.value : this.remoteId,
    contractId: contractId ?? this.contractId,
    teamId: teamId ?? this.teamId,
    formTemplateVersionId: formTemplateVersionId ?? this.formTemplateVersionId,
    collectorUserId: collectorUserId ?? this.collectorUserId,
    answersJson: answersJson ?? this.answersJson,
    syncStatus: syncStatus ?? this.syncStatus,
    syncError: syncError.present ? syncError.value : this.syncError,
    createdAt: createdAt ?? this.createdAt,
    updatedAt: updatedAt ?? this.updatedAt,
  );
  LocalRda copyWithCompanion(LocalRdasCompanion data) {
    return LocalRda(
      localId: data.localId.present ? data.localId.value : this.localId,
      remoteId: data.remoteId.present ? data.remoteId.value : this.remoteId,
      contractId: data.contractId.present
          ? data.contractId.value
          : this.contractId,
      teamId: data.teamId.present ? data.teamId.value : this.teamId,
      formTemplateVersionId: data.formTemplateVersionId.present
          ? data.formTemplateVersionId.value
          : this.formTemplateVersionId,
      collectorUserId: data.collectorUserId.present
          ? data.collectorUserId.value
          : this.collectorUserId,
      answersJson: data.answersJson.present
          ? data.answersJson.value
          : this.answersJson,
      syncStatus: data.syncStatus.present
          ? data.syncStatus.value
          : this.syncStatus,
      syncError: data.syncError.present ? data.syncError.value : this.syncError,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalRda(')
          ..write('localId: $localId, ')
          ..write('remoteId: $remoteId, ')
          ..write('contractId: $contractId, ')
          ..write('teamId: $teamId, ')
          ..write('formTemplateVersionId: $formTemplateVersionId, ')
          ..write('collectorUserId: $collectorUserId, ')
          ..write('answersJson: $answersJson, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('syncError: $syncError, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    localId,
    remoteId,
    contractId,
    teamId,
    formTemplateVersionId,
    collectorUserId,
    answersJson,
    syncStatus,
    syncError,
    createdAt,
    updatedAt,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalRda &&
          other.localId == this.localId &&
          other.remoteId == this.remoteId &&
          other.contractId == this.contractId &&
          other.teamId == this.teamId &&
          other.formTemplateVersionId == this.formTemplateVersionId &&
          other.collectorUserId == this.collectorUserId &&
          other.answersJson == this.answersJson &&
          other.syncStatus == this.syncStatus &&
          other.syncError == this.syncError &&
          other.createdAt == this.createdAt &&
          other.updatedAt == this.updatedAt);
}

class LocalRdasCompanion extends UpdateCompanion<LocalRda> {
  final Value<String> localId;
  final Value<String?> remoteId;
  final Value<String> contractId;
  final Value<String> teamId;
  final Value<String> formTemplateVersionId;
  final Value<String> collectorUserId;
  final Value<String> answersJson;
  final Value<LocalSyncStatus> syncStatus;
  final Value<String?> syncError;
  final Value<DateTime> createdAt;
  final Value<DateTime> updatedAt;
  final Value<int> rowid;
  const LocalRdasCompanion({
    this.localId = const Value.absent(),
    this.remoteId = const Value.absent(),
    this.contractId = const Value.absent(),
    this.teamId = const Value.absent(),
    this.formTemplateVersionId = const Value.absent(),
    this.collectorUserId = const Value.absent(),
    this.answersJson = const Value.absent(),
    this.syncStatus = const Value.absent(),
    this.syncError = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  LocalRdasCompanion.insert({
    required String localId,
    this.remoteId = const Value.absent(),
    required String contractId,
    required String teamId,
    required String formTemplateVersionId,
    required String collectorUserId,
    required String answersJson,
    required LocalSyncStatus syncStatus,
    this.syncError = const Value.absent(),
    required DateTime createdAt,
    required DateTime updatedAt,
    this.rowid = const Value.absent(),
  }) : localId = Value(localId),
       contractId = Value(contractId),
       teamId = Value(teamId),
       formTemplateVersionId = Value(formTemplateVersionId),
       collectorUserId = Value(collectorUserId),
       answersJson = Value(answersJson),
       syncStatus = Value(syncStatus),
       createdAt = Value(createdAt),
       updatedAt = Value(updatedAt);
  static Insertable<LocalRda> custom({
    Expression<String>? localId,
    Expression<String>? remoteId,
    Expression<String>? contractId,
    Expression<String>? teamId,
    Expression<String>? formTemplateVersionId,
    Expression<String>? collectorUserId,
    Expression<String>? answersJson,
    Expression<String>? syncStatus,
    Expression<String>? syncError,
    Expression<DateTime>? createdAt,
    Expression<DateTime>? updatedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (localId != null) 'local_id': localId,
      if (remoteId != null) 'remote_id': remoteId,
      if (contractId != null) 'contract_id': contractId,
      if (teamId != null) 'team_id': teamId,
      if (formTemplateVersionId != null)
        'form_template_version_id': formTemplateVersionId,
      if (collectorUserId != null) 'collector_user_id': collectorUserId,
      if (answersJson != null) 'answers_json': answersJson,
      if (syncStatus != null) 'sync_status': syncStatus,
      if (syncError != null) 'sync_error': syncError,
      if (createdAt != null) 'created_at': createdAt,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  LocalRdasCompanion copyWith({
    Value<String>? localId,
    Value<String?>? remoteId,
    Value<String>? contractId,
    Value<String>? teamId,
    Value<String>? formTemplateVersionId,
    Value<String>? collectorUserId,
    Value<String>? answersJson,
    Value<LocalSyncStatus>? syncStatus,
    Value<String?>? syncError,
    Value<DateTime>? createdAt,
    Value<DateTime>? updatedAt,
    Value<int>? rowid,
  }) {
    return LocalRdasCompanion(
      localId: localId ?? this.localId,
      remoteId: remoteId ?? this.remoteId,
      contractId: contractId ?? this.contractId,
      teamId: teamId ?? this.teamId,
      formTemplateVersionId:
          formTemplateVersionId ?? this.formTemplateVersionId,
      collectorUserId: collectorUserId ?? this.collectorUserId,
      answersJson: answersJson ?? this.answersJson,
      syncStatus: syncStatus ?? this.syncStatus,
      syncError: syncError ?? this.syncError,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (localId.present) {
      map['local_id'] = Variable<String>(localId.value);
    }
    if (remoteId.present) {
      map['remote_id'] = Variable<String>(remoteId.value);
    }
    if (contractId.present) {
      map['contract_id'] = Variable<String>(contractId.value);
    }
    if (teamId.present) {
      map['team_id'] = Variable<String>(teamId.value);
    }
    if (formTemplateVersionId.present) {
      map['form_template_version_id'] = Variable<String>(
        formTemplateVersionId.value,
      );
    }
    if (collectorUserId.present) {
      map['collector_user_id'] = Variable<String>(collectorUserId.value);
    }
    if (answersJson.present) {
      map['answers_json'] = Variable<String>(answersJson.value);
    }
    if (syncStatus.present) {
      map['sync_status'] = Variable<String>(
        $LocalRdasTable.$convertersyncStatus.toSql(syncStatus.value),
      );
    }
    if (syncError.present) {
      map['sync_error'] = Variable<String>(syncError.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<DateTime>(updatedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalRdasCompanion(')
          ..write('localId: $localId, ')
          ..write('remoteId: $remoteId, ')
          ..write('contractId: $contractId, ')
          ..write('teamId: $teamId, ')
          ..write('formTemplateVersionId: $formTemplateVersionId, ')
          ..write('collectorUserId: $collectorUserId, ')
          ..write('answersJson: $answersJson, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('syncError: $syncError, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $CachedFormVersionsTable cachedFormVersions =
      $CachedFormVersionsTable(this);
  late final $LocalRdasTable localRdas = $LocalRdasTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    cachedFormVersions,
    localRdas,
  ];
}

typedef $$CachedFormVersionsTableCreateCompanionBuilder =
    CachedFormVersionsCompanion Function({
      required String id,
      required String templateId,
      required String contractId,
      required int versionNumber,
      required String fieldsJson,
      required DateTime cachedAt,
      Value<int> rowid,
    });
typedef $$CachedFormVersionsTableUpdateCompanionBuilder =
    CachedFormVersionsCompanion Function({
      Value<String> id,
      Value<String> templateId,
      Value<String> contractId,
      Value<int> versionNumber,
      Value<String> fieldsJson,
      Value<DateTime> cachedAt,
      Value<int> rowid,
    });

class $$CachedFormVersionsTableFilterComposer
    extends Composer<_$AppDatabase, $CachedFormVersionsTable> {
  $$CachedFormVersionsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get templateId => $composableBuilder(
    column: $table.templateId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get contractId => $composableBuilder(
    column: $table.contractId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get versionNumber => $composableBuilder(
    column: $table.versionNumber,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get fieldsJson => $composableBuilder(
    column: $table.fieldsJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get cachedAt => $composableBuilder(
    column: $table.cachedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedFormVersionsTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedFormVersionsTable> {
  $$CachedFormVersionsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get templateId => $composableBuilder(
    column: $table.templateId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get contractId => $composableBuilder(
    column: $table.contractId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get versionNumber => $composableBuilder(
    column: $table.versionNumber,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get fieldsJson => $composableBuilder(
    column: $table.fieldsJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get cachedAt => $composableBuilder(
    column: $table.cachedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedFormVersionsTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedFormVersionsTable> {
  $$CachedFormVersionsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get templateId => $composableBuilder(
    column: $table.templateId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get contractId => $composableBuilder(
    column: $table.contractId,
    builder: (column) => column,
  );

  GeneratedColumn<int> get versionNumber => $composableBuilder(
    column: $table.versionNumber,
    builder: (column) => column,
  );

  GeneratedColumn<String> get fieldsJson => $composableBuilder(
    column: $table.fieldsJson,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get cachedAt =>
      $composableBuilder(column: $table.cachedAt, builder: (column) => column);
}

class $$CachedFormVersionsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CachedFormVersionsTable,
          CachedFormVersion,
          $$CachedFormVersionsTableFilterComposer,
          $$CachedFormVersionsTableOrderingComposer,
          $$CachedFormVersionsTableAnnotationComposer,
          $$CachedFormVersionsTableCreateCompanionBuilder,
          $$CachedFormVersionsTableUpdateCompanionBuilder,
          (
            CachedFormVersion,
            BaseReferences<
              _$AppDatabase,
              $CachedFormVersionsTable,
              CachedFormVersion
            >,
          ),
          CachedFormVersion,
          PrefetchHooks Function()
        > {
  $$CachedFormVersionsTableTableManager(
    _$AppDatabase db,
    $CachedFormVersionsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedFormVersionsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedFormVersionsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedFormVersionsTableAnnotationComposer(
                $db: db,
                $table: table,
              ),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String> templateId = const Value.absent(),
                Value<String> contractId = const Value.absent(),
                Value<int> versionNumber = const Value.absent(),
                Value<String> fieldsJson = const Value.absent(),
                Value<DateTime> cachedAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedFormVersionsCompanion(
                id: id,
                templateId: templateId,
                contractId: contractId,
                versionNumber: versionNumber,
                fieldsJson: fieldsJson,
                cachedAt: cachedAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required String templateId,
                required String contractId,
                required int versionNumber,
                required String fieldsJson,
                required DateTime cachedAt,
                Value<int> rowid = const Value.absent(),
              }) => CachedFormVersionsCompanion.insert(
                id: id,
                templateId: templateId,
                contractId: contractId,
                versionNumber: versionNumber,
                fieldsJson: fieldsJson,
                cachedAt: cachedAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedFormVersionsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CachedFormVersionsTable,
      CachedFormVersion,
      $$CachedFormVersionsTableFilterComposer,
      $$CachedFormVersionsTableOrderingComposer,
      $$CachedFormVersionsTableAnnotationComposer,
      $$CachedFormVersionsTableCreateCompanionBuilder,
      $$CachedFormVersionsTableUpdateCompanionBuilder,
      (
        CachedFormVersion,
        BaseReferences<
          _$AppDatabase,
          $CachedFormVersionsTable,
          CachedFormVersion
        >,
      ),
      CachedFormVersion,
      PrefetchHooks Function()
    >;
typedef $$LocalRdasTableCreateCompanionBuilder =
    LocalRdasCompanion Function({
      required String localId,
      Value<String?> remoteId,
      required String contractId,
      required String teamId,
      required String formTemplateVersionId,
      required String collectorUserId,
      required String answersJson,
      required LocalSyncStatus syncStatus,
      Value<String?> syncError,
      required DateTime createdAt,
      required DateTime updatedAt,
      Value<int> rowid,
    });
typedef $$LocalRdasTableUpdateCompanionBuilder =
    LocalRdasCompanion Function({
      Value<String> localId,
      Value<String?> remoteId,
      Value<String> contractId,
      Value<String> teamId,
      Value<String> formTemplateVersionId,
      Value<String> collectorUserId,
      Value<String> answersJson,
      Value<LocalSyncStatus> syncStatus,
      Value<String?> syncError,
      Value<DateTime> createdAt,
      Value<DateTime> updatedAt,
      Value<int> rowid,
    });

class $$LocalRdasTableFilterComposer
    extends Composer<_$AppDatabase, $LocalRdasTable> {
  $$LocalRdasTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get localId => $composableBuilder(
    column: $table.localId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get remoteId => $composableBuilder(
    column: $table.remoteId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get contractId => $composableBuilder(
    column: $table.contractId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get teamId => $composableBuilder(
    column: $table.teamId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get formTemplateVersionId => $composableBuilder(
    column: $table.formTemplateVersionId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get collectorUserId => $composableBuilder(
    column: $table.collectorUserId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get answersJson => $composableBuilder(
    column: $table.answersJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnWithTypeConverterFilters<LocalSyncStatus, LocalSyncStatus, String>
  get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnWithTypeConverterFilters(column),
  );

  ColumnFilters<String> get syncError => $composableBuilder(
    column: $table.syncError,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$LocalRdasTableOrderingComposer
    extends Composer<_$AppDatabase, $LocalRdasTable> {
  $$LocalRdasTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get localId => $composableBuilder(
    column: $table.localId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get remoteId => $composableBuilder(
    column: $table.remoteId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get contractId => $composableBuilder(
    column: $table.contractId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get teamId => $composableBuilder(
    column: $table.teamId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get formTemplateVersionId => $composableBuilder(
    column: $table.formTemplateVersionId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get collectorUserId => $composableBuilder(
    column: $table.collectorUserId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get answersJson => $composableBuilder(
    column: $table.answersJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncError => $composableBuilder(
    column: $table.syncError,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$LocalRdasTableAnnotationComposer
    extends Composer<_$AppDatabase, $LocalRdasTable> {
  $$LocalRdasTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get localId =>
      $composableBuilder(column: $table.localId, builder: (column) => column);

  GeneratedColumn<String> get remoteId =>
      $composableBuilder(column: $table.remoteId, builder: (column) => column);

  GeneratedColumn<String> get contractId => $composableBuilder(
    column: $table.contractId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get teamId =>
      $composableBuilder(column: $table.teamId, builder: (column) => column);

  GeneratedColumn<String> get formTemplateVersionId => $composableBuilder(
    column: $table.formTemplateVersionId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get collectorUserId => $composableBuilder(
    column: $table.collectorUserId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get answersJson => $composableBuilder(
    column: $table.answersJson,
    builder: (column) => column,
  );

  GeneratedColumnWithTypeConverter<LocalSyncStatus, String> get syncStatus =>
      $composableBuilder(
        column: $table.syncStatus,
        builder: (column) => column,
      );

  GeneratedColumn<String> get syncError =>
      $composableBuilder(column: $table.syncError, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<DateTime> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);
}

class $$LocalRdasTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $LocalRdasTable,
          LocalRda,
          $$LocalRdasTableFilterComposer,
          $$LocalRdasTableOrderingComposer,
          $$LocalRdasTableAnnotationComposer,
          $$LocalRdasTableCreateCompanionBuilder,
          $$LocalRdasTableUpdateCompanionBuilder,
          (LocalRda, BaseReferences<_$AppDatabase, $LocalRdasTable, LocalRda>),
          LocalRda,
          PrefetchHooks Function()
        > {
  $$LocalRdasTableTableManager(_$AppDatabase db, $LocalRdasTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalRdasTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalRdasTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalRdasTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> localId = const Value.absent(),
                Value<String?> remoteId = const Value.absent(),
                Value<String> contractId = const Value.absent(),
                Value<String> teamId = const Value.absent(),
                Value<String> formTemplateVersionId = const Value.absent(),
                Value<String> collectorUserId = const Value.absent(),
                Value<String> answersJson = const Value.absent(),
                Value<LocalSyncStatus> syncStatus = const Value.absent(),
                Value<String?> syncError = const Value.absent(),
                Value<DateTime> createdAt = const Value.absent(),
                Value<DateTime> updatedAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => LocalRdasCompanion(
                localId: localId,
                remoteId: remoteId,
                contractId: contractId,
                teamId: teamId,
                formTemplateVersionId: formTemplateVersionId,
                collectorUserId: collectorUserId,
                answersJson: answersJson,
                syncStatus: syncStatus,
                syncError: syncError,
                createdAt: createdAt,
                updatedAt: updatedAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String localId,
                Value<String?> remoteId = const Value.absent(),
                required String contractId,
                required String teamId,
                required String formTemplateVersionId,
                required String collectorUserId,
                required String answersJson,
                required LocalSyncStatus syncStatus,
                Value<String?> syncError = const Value.absent(),
                required DateTime createdAt,
                required DateTime updatedAt,
                Value<int> rowid = const Value.absent(),
              }) => LocalRdasCompanion.insert(
                localId: localId,
                remoteId: remoteId,
                contractId: contractId,
                teamId: teamId,
                formTemplateVersionId: formTemplateVersionId,
                collectorUserId: collectorUserId,
                answersJson: answersJson,
                syncStatus: syncStatus,
                syncError: syncError,
                createdAt: createdAt,
                updatedAt: updatedAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$LocalRdasTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $LocalRdasTable,
      LocalRda,
      $$LocalRdasTableFilterComposer,
      $$LocalRdasTableOrderingComposer,
      $$LocalRdasTableAnnotationComposer,
      $$LocalRdasTableCreateCompanionBuilder,
      $$LocalRdasTableUpdateCompanionBuilder,
      (LocalRda, BaseReferences<_$AppDatabase, $LocalRdasTable, LocalRda>),
      LocalRda,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$CachedFormVersionsTableTableManager get cachedFormVersions =>
      $$CachedFormVersionsTableTableManager(_db, _db.cachedFormVersions);
  $$LocalRdasTableTableManager get localRdas =>
      $$LocalRdasTableTableManager(_db, _db.localRdas);
}
