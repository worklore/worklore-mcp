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
  // Text fields fire onChanged on every keystroke; these make sure the
  // "started" events go out once per visit to this screen.
  bool _emailStartedFired = false;
  bool _phoneStartedFired = false;

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
                setState(() {});
                if (!_emailStartedFired) {
                  _emailStartedFired = true;
                  Analytics.capture('registration_email_started');
                }
              },
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _phone,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(labelText: 'Phone'),
              onChanged: (_) {
                setState(() {});
                if (!_phoneStartedFired) {
                  _phoneStartedFired = true;
                  Analytics.capture('registration_phone_started');
                }
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
              // Once per drag, on release. onChanged fires for every step.
              onChangeEnd: (v) => Analytics.capture(
                'loan_amount_changed',
                {'amount': v.round()},
              ),
            ),
            CheckboxListTile(
              value: _terms,
              title: const Text('I accept the terms and conditions'),
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (v) {
                setState(() => _terms = v ?? false);
                if (_terms) Analytics.capture('terms_accepted');
              },
            ),
            const Spacer(),
            FilledButton(
              onPressed: _canContinue
                  ? () {
                      Analytics.capture('registration_continue_tapped', {
                        'amount': _amount.round(),
                        'terms': _terms,
                      });
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
