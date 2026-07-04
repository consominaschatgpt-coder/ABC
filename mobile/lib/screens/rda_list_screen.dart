import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/auth_controller.dart';
import '../db/app_database.dart';
import '../repositories/form_template_repository.dart';
import '../repositories/rda_repository.dart';
import 'login_screen.dart';
import 'rda_form_screen.dart';

class RdaListScreen extends StatelessWidget {
  const RdaListScreen({super.key});

  String _statusLabel(LocalSyncStatus status) {
    switch (status) {
      case LocalSyncStatus.rascunhoLocal:
        return 'Rascunho (local)';
      case LocalSyncStatus.filaEnvio:
        return 'Na fila de envio';
      case LocalSyncStatus.enviando:
        return 'Enviando...';
      case LocalSyncStatus.sincronizado:
        return 'Sincronizado';
      case LocalSyncStatus.erro:
        return 'Erro — será tentado de novo';
    }
  }

  Color _statusColor(LocalSyncStatus status) {
    switch (status) {
      case LocalSyncStatus.rascunhoLocal:
        return Colors.grey;
      case LocalSyncStatus.filaEnvio:
        return Colors.blue;
      case LocalSyncStatus.enviando:
        return Colors.orange;
      case LocalSyncStatus.sincronizado:
        return Colors.green;
      case LocalSyncStatus.erro:
        return Colors.red;
    }
  }

  Future<void> _createRda(BuildContext context) async {
    final auth = context.read<AuthController>();
    final teams = auth.teams;
    if (teams.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Você ainda não está vinculado a nenhuma equipe.')));
      return;
    }

    final team = teams.length == 1
        ? teams.first
        : await showDialog(
            context: context,
            builder: (context) => SimpleDialog(
              title: const Text('Escolha a equipe'),
              children: [
                for (final t in teams)
                  SimpleDialogOption(onPressed: () => Navigator.pop(context, t), child: Text(t.name)),
              ],
            ),
          );
    if (team == null || !context.mounted) return;

    final formRepo = context.read<FormTemplateRepository>();
    final formVersionId = await formRepo.formVersionIdForContract(team.contractId);
    if (formVersionId == null) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Nenhum formulário disponível offline para este contrato ainda.')),
      );
      return;
    }
    if (!context.mounted) return;

    final rdaRepo = context.read<RdaRepository>();
    final draft = await rdaRepo.createDraft(
      contractId: team.contractId,
      teamId: team.id,
      formTemplateVersionId: formVersionId,
      collectorUserId: auth.user!.id,
    );

    if (!context.mounted) return;
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => RdaFormScreen(localId: draft.localId)));
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthController>();
    final rdaRepo = context.read<RdaRepository>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('RDAs'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await auth.logout();
              if (!context.mounted) return;
              Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const LoginScreen()));
            },
          ),
        ],
      ),
      body: StreamBuilder<List<LocalRda>>(
        stream: rdaRepo.watchForCollector(auth.user!.id),
        builder: (context, snapshot) {
          final items = snapshot.data ?? const [];
          if (items.isEmpty) {
            return const Center(child: Text('Nenhum RDA ainda. Toque em + para criar.'));
          }
          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, index) {
              final item = items[index];
              return ListTile(
                title: Text('RDA de ${item.createdAt.toLocal()}'.split('.').first),
                subtitle: Text(
                  _statusLabel(item.syncStatus),
                  style: TextStyle(color: _statusColor(item.syncStatus)),
                ),
                onTap: () => Navigator.of(
                  context,
                ).push(MaterialPageRoute(builder: (_) => RdaFormScreen(localId: item.localId))),
              );
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _createRda(context),
        child: const Icon(Icons.add),
      ),
    );
  }
}
