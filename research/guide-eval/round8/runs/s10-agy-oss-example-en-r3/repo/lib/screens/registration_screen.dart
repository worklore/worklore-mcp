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

  // Flags to ensure events fire only once per screen visit
  bool _emailStartedFired = false;
  bool _phoneStartedFired = false;
  bool _loanChangedFired = false;
  bool _termsAcceptedFired = false;
  bool _continueTappedFired = false; // optional guard

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
                if (!_emailStartedFired) {
                  Analytics.capture('registration_email_started');
                  _emailStartedFired = true;
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
                if (!_phoneStartedFired) {
                  Analytics.capture('registration_phone_started');
                  _phoneStartedFired = true;
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
                if (!_loanChangedFired) {
                  Analytics.capture('loan_amount_changed', {'amount': v.round()});
                  _loanChangedFired = true;
                }
              },
            ),
            CheckboxListTile(
              value: _terms,
              title: const Text('I accept the terms and conditions'),
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (v) {
                final newVal = v ?? false;
                if (newVal && !_termsAcceptedFired) {
                  Analytics.capture('terms_accepted');
                  _termsAcceptedFired = true;
                }
                setState(() => _terms = newVal);
              },
            ),
            const Spacer(),
            FilledButton(
              onPressed: _canContinue
                  ? () {
                      if (!_continueTappedFired) {
                        Analytics.capture('registration_continue_tapped', {
                          'amount': _amount.round(),
                          'terms': _terms,
                        });
                        _continueTappedFired = true;
                      }
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
