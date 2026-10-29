// Registration screen with analytics events
import 'package:flutter/material.dart';
import '../analytics.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  // Tracking flags to ensure each event is sent only once
  bool _emailStarted = false;
  bool _phoneStarted = false;
  bool _termsAcceptedSent = false;
  bool _continueTappedSent = false;

  // Controllers and state
  final TextEditingController _email = TextEditingController();
  final TextEditingController _phone = TextEditingController();
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
            // Email field – fire "registration_email_started" on first change
            TextField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(labelText: 'Email'),
              onChanged: (value) {
                if (!_emailStarted) {
                  _emailStarted = true;
                  Analytics.capture('registration_email_started');
                }
                setState(() {});
              },
            ),
            const SizedBox(height: 12),
            // Phone field – fire "registration_phone_started" on first change
            TextField(
              controller: _phone,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(labelText: 'Phone'),
              onChanged: (value) {
                if (!_phoneStarted) {
                  _phoneStarted = true;
                  Analytics.capture('registration_phone_started');
                }
                setState(() {});
              },
            ),
            const SizedBox(height: 24),
            // Loan amount slider – fire "loan_amount_changed" on each change
            Text('Loan amount: ${_amount.round()}'),
            Slider(
              min: 10000,
              max: 500000,
              divisions: 49,
              value: _amount,
              label: _amount.round().toString(),
              onChanged: (v) {
                setState(() => _amount = v);
                Analytics.capture('loan_amount_changed', {
                  'amount': v.round(),
                });
              },
            ),
            // Terms checkbox – fire "terms_accepted" when checked the first time
            CheckboxListTile(
              value: _terms,
              title: const Text('I accept the terms and conditions'),
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (v) {
                final newValue = v ?? false;
                setState(() => _terms = newValue);
                if (newValue && !_termsAcceptedSent) {
                  _termsAcceptedSent = true;
                  Analytics.capture('terms_accepted');
                }
              },
            ),
            const Spacer(),
            // Continue button – fire "registration_continue_tapped" once
            FilledButton(
              onPressed: _canContinue
                  ? () {
                      if (!_continueTappedSent) {
                        _continueTappedSent = true;
                        Analytics.capture('registration_continue_tapped', {
                          'amount': _amount.round(),
                          'terms': _terms,
                        });
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
