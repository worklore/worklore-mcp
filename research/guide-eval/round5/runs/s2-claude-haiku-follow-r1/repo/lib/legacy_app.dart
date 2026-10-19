import 'package:flutter/material.dart';
import 'package:posthog_flutter/posthog_flutter.dart';

import 'screens/calculator_screen.dart';
import 'screens/application_screen.dart';

/// The old shell. Kept for the A/B group until the redesign is fully rolled out.
class LegacyApp extends StatelessWidget {
  const LegacyApp({super.key});

  @override
  Widget build(BuildContext context) {
    // PostHogWidget must wrap the app: session replay captures screenshots
    // from it. Without it, events arrive but replays stay empty.
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
