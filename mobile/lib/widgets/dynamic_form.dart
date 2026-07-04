import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:signature/signature.dart';

import '../models/field_definition.dart';

/// Renderiza o RDA a partir da lista de campos do FormTemplateVersion —
/// o mesmo JSON usado pelo backend e pelo painel web. Campos condicionais
/// aparecem/desaparecem em tempo real conforme as respostas.
class DynamicForm extends StatefulWidget {
  final List<FieldDefinition> fields;
  final Map<String, dynamic> initialAnswers;
  final ValueChanged<Map<String, dynamic>> onChanged;
  final bool readOnly;

  const DynamicForm({
    super.key,
    required this.fields,
    required this.initialAnswers,
    required this.onChanged,
    this.readOnly = false,
  });

  @override
  State<DynamicForm> createState() => DynamicFormState();
}

class DynamicFormState extends State<DynamicForm> {
  late Map<String, dynamic> _answers;

  @override
  void initState() {
    super.initState();
    _answers = Map<String, dynamic>.from(widget.initialAnswers);
  }

  void _setAnswer(String key, dynamic value) {
    setState(() => _answers[key] = value);
    widget.onChanged(Map<String, dynamic>.from(_answers));
  }

  @override
  Widget build(BuildContext context) {
    final sortedFields = [...widget.fields]..sort((a, b) => a.order.compareTo(b.order));
    final activeFields = sortedFields.where((f) => f.isActive(_answers)).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final field in activeFields) ...[
          _FieldEditor(
            field: field,
            value: _answers[field.key],
            readOnly: widget.readOnly,
            onChanged: (value) => _setAnswer(field.key, value),
          ),
          const SizedBox(height: 16),
        ],
      ],
    );
  }
}

class _FieldEditor extends StatelessWidget {
  final FieldDefinition field;
  final dynamic value;
  final bool readOnly;
  final ValueChanged<dynamic> onChanged;

  const _FieldEditor({
    required this.field,
    required this.value,
    required this.readOnly,
    required this.onChanged,
  });

  String get _label => field.required ? '${field.label} *' : field.label;

  @override
  Widget build(BuildContext context) {
    switch (field.type) {
      case FieldType.texto:
        return TextFormField(
          key: Key('field_${field.key}'),
          initialValue: value as String? ?? '',
          decoration: InputDecoration(labelText: _label),
          enabled: !readOnly,
          onChanged: onChanged,
        );
      case FieldType.numero:
        return TextFormField(
          key: Key('field_${field.key}'),
          initialValue: value?.toString() ?? '',
          decoration: InputDecoration(labelText: _label),
          keyboardType: TextInputType.number,
          enabled: !readOnly,
          onChanged: (text) => onChanged(num.tryParse(text)),
        );
      case FieldType.dataHora:
        return _DateTimeField(label: _label, value: value as String?, readOnly: readOnly, onChanged: onChanged);
      case FieldType.selecaoUnica:
        return DropdownButtonFormField<String>(
          key: Key('field_${field.key}'),
          initialValue: value as String?,
          decoration: InputDecoration(labelText: _label),
          items: [
            for (final option in field.options ?? const [])
              DropdownMenuItem(value: option, child: Text(option)),
          ],
          onChanged: readOnly ? null : onChanged,
        );
      case FieldType.selecaoMultipla:
        final selected = (value as List?)?.cast<String>() ?? const <String>[];
        return _MultiSelectField(
          label: _label,
          options: field.options ?? const [],
          selected: selected,
          readOnly: readOnly,
          onChanged: onChanged,
        );
      case FieldType.foto:
        return _PhotoField(label: _label, value: value as String?, readOnly: readOnly, onChanged: onChanged);
      case FieldType.assinatura:
        return _SignatureField(label: _label, readOnly: readOnly, onChanged: onChanged);
      case FieldType.localizacao:
        return _LocationField(label: _label, value: value as String?, readOnly: readOnly, onChanged: onChanged);
    }
  }
}

class _DateTimeField extends StatelessWidget {
  final String label;
  final String? value;
  final bool readOnly;
  final ValueChanged<dynamic> onChanged;

  const _DateTimeField({required this.label, required this.value, required this.readOnly, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      readOnly: true,
      enabled: !readOnly,
      decoration: InputDecoration(labelText: label, suffixIcon: const Icon(Icons.calendar_today)),
      controller: TextEditingController(text: value ?? ''),
      onTap: readOnly
          ? null
          : () async {
              final now = DateTime.now();
              final date = await showDatePicker(
                context: context,
                initialDate: now,
                firstDate: DateTime(now.year - 1),
                lastDate: DateTime(now.year + 1),
              );
              if (date == null || !context.mounted) return;
              final time = await showTimePicker(context: context, initialTime: TimeOfDay.now());
              if (time == null) return;
              final combined = DateTime(date.year, date.month, date.day, time.hour, time.minute);
              onChanged(combined.toIso8601String());
            },
    );
  }
}

class _MultiSelectField extends StatelessWidget {
  final String label;
  final List<String> options;
  final List<String> selected;
  final bool readOnly;
  final ValueChanged<dynamic> onChanged;

  const _MultiSelectField({
    required this.label,
    required this.options,
    required this.selected,
    required this.readOnly,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.labelLarge),
        for (final option in options)
          CheckboxListTile(
            key: Key('option_$option'),
            dense: true,
            contentPadding: EdgeInsets.zero,
            title: Text(option),
            value: selected.contains(option),
            onChanged: readOnly
                ? null
                : (checked) {
                    final next = [...selected];
                    if (checked == true) {
                      next.add(option);
                    } else {
                      next.remove(option);
                    }
                    onChanged(next);
                  },
          ),
      ],
    );
  }
}

class _PhotoField extends StatelessWidget {
  final String label;
  final String? value;
  final bool readOnly;
  final ValueChanged<dynamic> onChanged;

  const _PhotoField({required this.label, required this.value, required this.readOnly, required this.onChanged});

  Future<void> _pick(ImageSource source) async {
    final picked = await ImagePicker().pickImage(source: source);
    if (picked != null) onChanged(picked.path);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.labelLarge),
        if (value != null) Text(value!, style: Theme.of(context).textTheme.bodySmall),
        if (!readOnly)
          Row(
            children: [
              TextButton.icon(
                onPressed: () => _pick(ImageSource.camera),
                icon: const Icon(Icons.camera_alt),
                label: const Text('Câmera'),
              ),
              TextButton.icon(
                onPressed: () => _pick(ImageSource.gallery),
                icon: const Icon(Icons.photo_library),
                label: const Text('Galeria'),
              ),
            ],
          ),
      ],
    );
  }
}

class _SignatureField extends StatefulWidget {
  final String label;
  final bool readOnly;
  final ValueChanged<dynamic> onChanged;

  const _SignatureField({required this.label, required this.readOnly, required this.onChanged});

  @override
  State<_SignatureField> createState() => _SignatureFieldState();
}

class _SignatureFieldState extends State<_SignatureField> {
  final _controller = SignatureController(penStrokeWidth: 2, penColor: Colors.black);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final bytes = await _controller.toPngBytes();
    if (bytes != null) widget.onChanged(base64Encode(bytes));
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(widget.label, style: Theme.of(context).textTheme.labelLarge),
        if (!widget.readOnly) ...[
          Container(
            height: 150,
            decoration: BoxDecoration(border: Border.all(color: Colors.grey)),
            child: Signature(controller: _controller, backgroundColor: Colors.white),
          ),
          Row(
            children: [
              TextButton(onPressed: _controller.clear, child: const Text('Limpar')),
              TextButton(onPressed: _save, child: const Text('Salvar assinatura')),
            ],
          ),
        ],
      ],
    );
  }
}

class _LocationField extends StatelessWidget {
  final String label;
  final String? value;
  final bool readOnly;
  final ValueChanged<dynamic> onChanged;

  const _LocationField({required this.label, required this.value, required this.readOnly, required this.onChanged});

  Future<void> _capture() async {
    final permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      await Geolocator.requestPermission();
    }
    final position = await Geolocator.getCurrentPosition();
    onChanged('${position.latitude},${position.longitude}');
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(child: Text('$label: ${value ?? "não capturada"}')),
        if (!readOnly) IconButton(icon: const Icon(Icons.my_location), onPressed: _capture),
      ],
    );
  }
}
