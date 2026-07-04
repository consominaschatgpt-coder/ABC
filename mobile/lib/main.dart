import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/api_client.dart';
import 'core/auth_controller.dart';
import 'core/auth_repository.dart';
import 'core/session_store.dart';
import 'db/app_database.dart';
import 'repositories/form_template_repository.dart';
import 'repositories/rda_repository.dart';
import 'screens/login_screen.dart';
import 'screens/rda_list_screen.dart';
import 'sync/sync_engine.dart';

/// Aponte para o backend real (ver ../../backend/README.md). Em produção
/// isso viraria uma variavel de build (--dart-define), mas para o escopo
/// desta fase mantemos um valor fixo, facil de trocar.
const apiBaseUrl = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000');

void main() {
  final db = AppDatabase();
  final api = ApiClient(baseUrl: apiBaseUrl);
  final sessionStore = SessionStore();
  final authRepository = AuthRepository(api: api, sessionStore: sessionStore);
  final formTemplateRepository = FormTemplateRepository(api: api, db: db);
  final rdaRepository = RdaRepository(db);
  final syncEngine = SyncEngine(db: db, api: api)..start();

  runApp(
    MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        Provider<ApiClient>.value(value: api),
        Provider<FormTemplateRepository>.value(value: formTemplateRepository),
        Provider<RdaRepository>.value(value: rdaRepository),
        Provider<SyncEngine>.value(value: syncEngine),
        ChangeNotifierProvider<AuthController>(
          create: (_) => AuthController(
            repository: authRepository,
            sessionStore: sessionStore,
            onContractAvailable: formTemplateRepository.refreshForContract,
          ),
        ),
      ],
      child: const RdaCampoApp(),
    ),
  );
}

class RdaCampoApp extends StatelessWidget {
  const RdaCampoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RDA de Campo',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple)),
      home: const _StartupGate(),
    );
  }
}

class _StartupGate extends StatelessWidget {
  const _StartupGate();

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthController>();
    if (auth.loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return auth.user == null ? const LoginScreen() : const RdaListScreen();
  }
}
