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
  bool _emailStartedSent = false;
  bool _phoneStartedSent = false;

  @override
  void dispose() {
    _email.dispose();
    _phone.dispose();
    super.dispose();
  }

  bool get _canContinue =>
      _terms && _email.text.contains('@') && _phone.text.length >= 10;

  void _onEmailChanged(String value) {
    // Sent once per visit, on the first character. The value is PII, so it is not sent.
    if (!_emailStartedSent && value.isNotEmpty) {
      _emailStartedSent = true;
      Analytics.capture('registration_email_started');
    }
    setState(() {});
  }

  void _onPhoneChanged(String value) {
    // Sent once per visit, on the first digit. The value is PII, so it is not sent.
    if (!_phoneStartedSent && value.isNotEmpty) {
      _phoneStartedSent = true;
      Analytics.capture('registration_phone_started');
    }
    setState(() {});
  }

  void _onContinue() {
    Analytics.capture('registration_continue_tapped', {
      'amount': _amount.round(),
      'terms': _terms,
    });
    Navigator.of(context).pushNamed('/offers');
  }

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
              onChanged: _onEmailChanged,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _phone,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(labelText: 'Phone'),
              onChanged: _onPhoneChanged,
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
              // Only the final value is sent; onChanged fires on every drag step.
              onChangeEnd: (v) => Analytics.capture('loan_amount_changed', {
                'amount': v.round(),
              }),
            ),
            CheckboxListTile(
              value: _terms,
              title: const Text('I accept the terms and conditions'),
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (v) {
                final accepted = v ?? false;
                if (accepted) Analytics.capture('terms_accepted');
                setState(() => _terms = accepted);
              },
            ),
            const Spacer(),
            FilledButton(
              onPressed: _canContinue ? _onContinue : null,
              child: const Text('Continue'),
            ),
          ],
        ),
      ),
    );
  }
}
