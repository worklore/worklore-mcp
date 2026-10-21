import 'package:flutter/material.dart';
import '../analytics.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  // Flags to ensure each event fires only once per screen visit
  bool _emailStartedFired = false;
  bool _phoneStartedFired = false;
  bool _loanAmountChangedFired = false;
  bool _termsAcceptedFired = false;

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
            // Email field – fire once on first edit
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
            // Phone field – fire once on first edit
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
            // Loan amount slider – capture once when the user releases the slider
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
            // Terms checkbox – fire once when the user checks it
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
            // Continue button – fire when tapped, include amount and terms
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
