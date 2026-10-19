import 'package:flutter/material.dart';
import 'package:posthog_flutter/posthog_flutter.dart';

import 'screens/calculator_screen.dart';
import 'screens/application_screen.dart';

/// The old shell. Kept for the A/B group until the redesign is fully rolled out.
class LegacyApp extends StatelessWidget {
  const LegacyApp({super.key});

  @override
  Widget build(BuildContext context) {
    // PostHogWidget is required for session replay: it captures the frames.
    // Without it events still arrive but recordings are empty. Do not remove.
    return PostHogWidget(
      child: MaterialApp(
        title: 'Loanly',
        theme: ThemeData(colorSchemeSeed: Colors.teal),
        navigatorObservers: [PosthogObserver()],
        routes: {
          '/': (_) => const CalculatorScreen(),
          '/apply': (_) => const ApplicationScreen(),
        },
      ),
    );
  }
}
