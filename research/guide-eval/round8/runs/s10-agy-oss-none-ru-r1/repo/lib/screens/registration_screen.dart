import 'package:flutter/material.dart';
import '../analytics.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  // Flags to ensure we capture start events only once
  bool _emailStarted = false;
  bool _phoneStarted = false;
  bool _termsAcceptedLogged = false;
  final _email = TextEditingController();
  final _phone = TextEditingController();
  double _amount = 50000;
  bool _terms = false;

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
              onChanged: (_) {
                if (!_phoneStarted) {
                  Analytics.capture('registration_phone_started');
                  _phoneStarted = true;
                }
                setState(() {});
              },
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _phone,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(labelText: 'Phone'),
              onChanged: (_) {
                if (!_phoneStarted) {
                  Analytics.capture('registration_phone_started');
                  _phoneStarted = true;
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
              onChanged: (v) {
                setState(() => _amount = v);
                Analytics.capture('loan_amount_changed', {'amount': v.round()});
              },
            ),
            CheckboxListTile(
              value: _terms,
              title: const Text('I accept the terms and conditions'),
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (v) {
                setState(() => _terms = v ?? false);
                if (!_termsAcceptedLogged && _terms) {
                  Analytics.capture('terms_accepted');
                  _termsAcceptedLogged = true;
                }
              },
            ),
            const Spacer(),
            FilledButton(
              onPressed: _canContinue
                  ? () => Navigator.of(context).pushNamed('/offers')
                  : null,
              child: const Text('Continue'),
            ),
          ],
        ),
      ),
    );
  }
}
