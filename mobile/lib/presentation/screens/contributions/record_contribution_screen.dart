import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:tontine_app/core/theme/app_theme.dart';

class RecordContributionScreen extends ConsumerStatefulWidget {
  const RecordContributionScreen({super.key});

  @override
  ConsumerState<RecordContributionScreen> createState() => _RecordContributionScreenState();
}

class _RecordContributionScreenState extends ConsumerState<RecordContributionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _commentController = TextEditingController();
  DateTime? _depositDate;
  String? _selectedMember;

  @override
  void dispose() {
    _amountController.dispose();
    _commentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Enregistrer un dépôt')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Member selection
              DropdownButtonFormField<String>(
                decoration: const InputDecoration(
                  labelText: 'Membre',
                  border: OutlineInputBorder(),
                ),
                items: const [],
                onChanged: (value) => setState(() => _selectedMember = value),
                validator: (value) => value == null ? 'Sélectionnez un membre' : null,
              ),
              const SizedBox(height: 16),
              // Amount
              TextFormField(
                controller: _amountController,
                decoration: const InputDecoration(
                  labelText: 'Montant (XOF)',
                  border: OutlineInputBorder(),
                  suffixText: 'XOF',
                ),
                keyboardType: TextInputType.number,
                validator: (value) {
                  if (value == null || value.isEmpty) return 'Entrez un montant';
                  final amount = int.tryParse(value);
                  if (amount == null || amount <= 0) return 'Montant invalide';
                  return null;
                },
              ),
              const SizedBox(height: 16),
              // Deposit date
              ListTile(
                title: Text(_depositDate == null
                    ? 'Date du dépôt'
                    : '${_depositDate!.day}/${_depositDate!.month}/${_depositDate!.year}'),
                trailing: const Icon(Icons.calendar_today),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                  side: const BorderSide(color: Colors.grey),
                ),
                onTap: () async {
                  final date = await showDatePicker(
                    context: context,
                    initialDate: DateTime.now(),
                    firstDate: DateTime(2020),
                    lastDate: DateTime.now(),
                  );
                  if (date != null) setState(() => _depositDate = date);
                },
              ),
              const SizedBox(height: 16),
              // Comment
              TextFormField(
                controller: _commentController,
                decoration: const InputDecoration(
                  labelText: 'Commentaire (facultatif)',
                  border: OutlineInputBorder(),
                ),
                maxLines: 3,
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () {
                  if (_formKey.currentState!.validate()) {
                    // Submit
                  }
                },
                child: const Text('Valider le dépôt'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
