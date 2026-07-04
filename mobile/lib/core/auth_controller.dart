import 'package:flutter/foundation.dart';

import '../models/user.dart';
import 'auth_repository.dart';
import 'session_store.dart';

class AuthController extends ChangeNotifier {
  final AuthRepository repository;
  final SessionStore sessionStore;
  final Future<void> Function(String contractId)? onContractAvailable;

  AppUser? user;
  List<Team> teams = const [];
  bool loading = true;

  AuthController({required this.repository, required this.sessionStore, this.onContractAvailable}) {
    _restore();
  }

  Future<void> _restore() async {
    user = await repository.restoreSession();
    teams = await sessionStore.readTeams();
    loading = false;
    notifyListeners();
  }

  Future<void> login(String email, String password) async {
    user = await repository.login(email, password);
    teams = await repository.myTeams();
    await sessionStore.saveTeams(teams);
    notifyListeners();

    if (onContractAvailable != null) {
      for (final contractId in teams.map((t) => t.contractId).toSet()) {
        try {
          await onContractAvailable!(contractId);
        } catch (_) {
          // melhor esforco: sem rede ou sem formulario publicado ainda,
          // o coletor so nao vai conseguir criar um RDA novo por enquanto
        }
      }
    }
  }

  Future<void> logout() async {
    await repository.logout();
    user = null;
    teams = const [];
    notifyListeners();
  }
}
