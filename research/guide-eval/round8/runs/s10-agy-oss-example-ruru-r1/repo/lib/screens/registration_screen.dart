import '../analytics.dart';
import 'package:flutter/material.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  final TextEditingController _email = TextEditingController();
  final TextEditingController _phone = TextEditingController();
  double _amount = 50000;
  bool _terms = false;

  // One‑time analytics flags per screen visit
  bool _emailInputFired = false;
  bool _phoneInputFired = false;
  bool _termsAcceptedFired = false;
  bool _loanAmountChangedFired = false;

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
                if (!_emailInputFired) {
                  Analytics.capture('registration_email_started');
                  _emailInputFired = true;
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
                if (!_phoneInputFired) {
                  Analytics.capture('registration_phone_started');
                  _phoneInputFired = true;
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
              onChangeEnd: (v) {
                if (!_loanAmountChangedFired) {
                  Analytics.capture('loan_amount_changed', {'amount': v.round()});
                  _loanAmountChangedFired = true;
                }
              },
            ),
            CheckboxListTile(
              value: _terms,
              title: const Text('I accept the terms and conditions'),
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (v) {
                final newValue = v ?? false;
                if (newValue && !_termsAcceptedFired) {
                  Analytics.capture('terms_accepted');
                  _termsAcceptedFired = true;
                }
                setState(() => _terms = newValue);
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
