import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/user.dart';

/// Guarda o token e os dados do usuario logado no aparelho, para o app
/// abrir direto na sessao mesmo sem rede (offline-first tambem vale pro
/// login, nao so pro RDA).
class SessionStore {
  static const _tokenKey = 'rda_campo.token';
  static const _userKey = 'rda_campo.user';
  static const _teamsKey = 'rda_campo.teams';

  final FlutterSecureStorage _storage;

  SessionStore({FlutterSecureStorage? storage}) : _storage = storage ?? const FlutterSecureStorage();

  Future<void> save(String token, AppUser user) async {
    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(key: _userKey, value: jsonEncode(user.toJson()));
  }

  Future<String?> readToken() => _storage.read(key: _tokenKey);

  Future<AppUser?> readUser() async {
    final raw = await _storage.read(key: _userKey);
    if (raw == null) return null;
    return AppUser.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  }

  /// As equipes sao cacheadas para o coletor conseguir criar um novo RDA
  /// mesmo sem rede (ele so precisa ter aberto o app online uma vez antes).
  Future<void> saveTeams(List<Team> teams) async {
    final encoded = jsonEncode(
      teams.map((t) => {'id': t.id, 'name': t.name, 'contract_id': t.contractId}).toList(),
    );
    await _storage.write(key: _teamsKey, value: encoded);
  }

  Future<List<Team>> readTeams() async {
    final raw = await _storage.read(key: _teamsKey);
    if (raw == null) return [];
    final list = jsonDecode(raw) as List<dynamic>;
    return list.map((e) => Team.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<void> clear() async {
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _userKey);
    await _storage.delete(key: _teamsKey);
  }
}
