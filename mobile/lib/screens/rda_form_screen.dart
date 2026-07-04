import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../db/app_database.dart';
import '../models/field_definition.dart';
import '../repositories/form_template_repository.dart';
import '../repositories/rda_repository.dart';
import '../widgets/dynamic_form.dart';

class RdaFormScreen extends StatefulWidget {
  final String localId;

  const RdaFormScreen({super.key, required this.localId});

  @override
  State<RdaFormScreen> createState() => _RdaFormScreenState();
}

class _RdaFormScreenState extends State<RdaFormScreen> {
  List<FieldDefinition>? _fields;
  Map<String, dynamic> _answers = {};
  String? _loadError;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final db = context.read<AppDatabase>();
    final formRepo = context.read<FormTemplateRepository>();

    final rda = await db.localRdaById(widget.localId);
    try {
      final fields = await formRepo.fieldsForVersionId(rda.formTemplateVersionId);
      if (!mounted) return;
      setState(() {
        _fields = fields;
        _answers = jsonDecode(rda.answersJson) as Map<String, dynamic>;
      });
    } catch (err) {
      if (!mounted) return;
      setState(() => _loadError = err.toString());
    }
  }

  Future<void> _onAnswersChanged(Map<String, dynamic> answers) async {
    _answers = answers;
    await context.read<RdaRepository>().updateAnswers(widget.localId, answers);
  }

  Future<void> _submit() async {
    final rdaRepo = context.read<RdaRepository>();
    try {
      await rdaRepo.markReadyToSend(widget.localId, _fields!);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('RDA na fila de envio — será sincronizado automaticamente.')),
      );
      Navigator.of(context).pop();
    } on ValidationException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.errors.join('; '))));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('RDA')),
      body: StreamBuilder<LocalRda>(
        stream: context.read<AppDatabase>().watchLocalRda(widget.localId),
        builder: (context, snapshot) {
          final rda = snapshot.data;
          final isDraft =
              rda == null ||
              rda.syncStatus == LocalSyncStatus.rascunhoLocal ||
              rda.syncStatus == LocalSyncStatus.erro;

          if (_loadError != null) {
            return Padding(
              padding: const EdgeInsets.all(16),
              child: Text('Não foi possível carregar o formulário: $_loadError'),
            );
          }
          if (_fields == null) {
            return const Center(child: CircularProgressIndicator());
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                DynamicForm(
                  key: const Key('dynamic_form'),
                  fields: _fields!,
                  initialAnswers: _answers,
                  readOnly: !isDraft,
                  onChanged: _onAnswersChanged,
                ),
                if (isDraft) ...[
                  const SizedBox(height: 16),
                  ElevatedButton(
                    key: const Key('submit_rda_button'),
                    onPressed: _submit,
                    child: const Text('Enviar RDA'),
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}
