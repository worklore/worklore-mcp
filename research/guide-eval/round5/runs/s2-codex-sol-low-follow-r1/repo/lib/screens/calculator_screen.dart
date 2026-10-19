import 'package:flutter/material.dart';

import '../analytics.dart';

class CalculatorScreen extends StatefulWidget {
  const CalculatorScreen({super.key});

  @override
  State<CalculatorScreen> createState() => _CalculatorScreenState();
}

class _CalculatorScreenState extends State<CalculatorScreen> {
  double _amount = 5000;
  int _months = 12;

  @override
  Widget build(BuildContext context) {
    final monthly = _amount * (1 + 0.012 * _months) / _months;
    return Scaffold(
      appBar: AppBar(title: const Text('Loan calculator')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Amount: ${_amount.round()}'),
            Slider(
              min: 1000,
              max: 50000,
              value: _amount,
              onChanged: (v) => setState(() => _amount = v),
              onChangeEnd: (v) =>
                  Analytics.track('loan_amount_changed', {'amount': v.round()}),
            ),
            Text('Months: $_months'),
            Slider(
              min: 3,
              max: 60,
              divisions: 57,
              value: _months.toDouble(),
              onChanged: (v) => setState(() => _months = v.round()),
              onChangeEnd: (v) =>
                  Analytics.track('loan_term_changed', {'months': v.round()}),
            ),
            const SizedBox(height: 24),
            Text('Monthly: ${monthly.toStringAsFixed(2)}',
                style: Theme.of(context).textTheme.headlineSmall),
            const Spacer(),
            FilledButton(
              onPressed: () {
                Analytics.track('apply_tapped');
                Navigator.of(context).pushNamed('/apply');
              },
              child: const Text('Apply'),
            ),
          ],
        ),
      ),
    );
  }
}
