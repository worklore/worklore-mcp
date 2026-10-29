import 'dart:async';

import 'package:flutter/material.dart';

import '../analytics.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  final _email = TextEditingController();
  final _phone = TextEditingController();
  double _amount = 50000;
  bool _terms = false;
  bool _emailStarted = false;
  bool _phoneStarted = false;

  @override
  void dispose() {
    _email.dispose();
    _phone.dispose();
    super.dispose();
  }

  bool get _canContinue =>
      _terms && _email.text.contains('@') && _phone.text.length >= 10;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Register')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(labelText: 'Email'),
              onChanged: (value) {
                if (value.isNotEmpty && !_emailStarted) {
                  _emailStarted = true;
                  unawaited(Analytics.capture('registration_email_started'));
                }
                setState(() {});
              },
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _phone,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(labelText: 'Phone'),
              onChanged: (value) {
                if (value.isNotEmpty && !_phoneStarted) {
                  _phoneStarted = true;
                  unawaited(Analytics.capture('registration_phone_started'));
                }
                setState(() {});
              },
            ),
            const SizedBox(height: 24),
            Text('Loan amount: ${_amount.round()}'),
            Slider(
              min: 10000,
              max: 500000,
              divisions: 49,
              value: _amount,
              label: _amount.round().toString(),
              onChanged: (v) => setState(() => _amount = v),
              onChangeEnd: (v) => unawaited(
                Analytics.capture('loan_amount_changed', {'amount': v.round()}),
              ),
            ),
            CheckboxListTile(
              value: _terms,
              title: const Text('I accept the terms and conditions'),
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (v) {
                if (v == true && !_terms) {
                  unawaited(Analytics.capture('terms_accepted'));
                }
                setState(() => _terms = v ?? false);
              },
            ),
            const Spacer(),
            FilledButton(
              onPressed: _canContinue
                  ? () {
                      unawaited(
                        Analytics.capture('registration_continue_tapped', {
                          'amount': _amount.round(),
                          'terms': _terms,
                        }),
                      );
                      Navigator.of(context).pushNamed('/offers');
                    }
                  : null,
              child: const Text('Continue'),
            ),
          ],
        ),
      ),
    );
  }
}
