import 'package:flutter/material.dart';

import '../analytics.dart';

class ApplicationScreen extends StatefulWidget {
  const ApplicationScreen({super.key});

  @override
  State<ApplicationScreen> createState() => _ApplicationScreenState();
}

class _ApplicationScreenState extends State<ApplicationScreen> {
  final _email = TextEditingController();
  bool _emailInputFired = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Apply')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _email,
              decoration: const InputDecoration(labelText: 'Email'),
              onChanged: (_) {
                if (!_emailInputFired) {
                  _emailInputFired = true;
                  Analytics.track('email_input');
                }
              },
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () {
                Analytics.track('application_submitted');
                ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Thanks, we will be in touch.')));
              },
              child: const Text('Submit'),
            ),
          ],
        ),
      ),
    );
  }
}
