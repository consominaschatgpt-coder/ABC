import '../models/user.dart';
import 'api_client.dart';
import 'session_store.dart';

class AuthRepository {
  final ApiClient api;
  final SessionStore sessionStore;

  AuthRepository({required this.api, required this.sessionStore});

  /// Tenta restaurar a sessao salva, sem bater na rede — permite abrir o
  /// app offline e continuar preenchendo RDAs.
  Future<AppUser?> restoreSession() async {
    final token = await sessionStore.readToken();
    final user = await sessionStore.readUser();
    if (token == null || user == null) return null;
    api.setToken(token);
    return user;
  }

  Future<AppUser> login(String email, String password) async {
    final response = await api.post('/auth/login', body: {'email': email, 'password': password});
    final token = response['access_token'] as String;
    api.setToken(token);

    final me = await api.get('/users/me');
    final user = AppUser.fromJson(me as Map<String, dynamic>);

    await sessionStore.save(token, user);
    return user;
  }

  Future<void> logout() async {
    api.setToken(null);
    await sessionStore.clear();
  }

  Future<List<Team>> myTeams() async {
    final response = await api.get('/users/me/teams') as List<dynamic>;
    return response.map((e) => Team.fromJson(e as Map<String, dynamic>)).toList();
  }
}
