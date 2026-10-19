import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:posthog_flutter/posthog_flutter.dart';

import 'screens/calculator_screen.dart';
import 'screens/application_screen.dart';
import 'screens/offers_screen.dart';

final _router = GoRouter(
  observers: [PosthogObserver()],
  routes: [
    GoRoute(path: '/', builder: (_, __) => const CalculatorScreen()),
    GoRoute(path: '/apply', builder: (_, __) => const ApplicationScreen()),
    GoRoute(path: '/offers', builder: (_, __) => const OffersScreen()),
  ],
);

/// The redesigned shell (default since 2.3.0).
class NewApp extends StatelessWidget {
  const NewApp({super.key});

  @override
  Widget build(BuildContext context) {
    // PostHogWidget is what captures the screenshots session replay is built
    // from. Without it events still arrive but replays stay empty. Do not
    // remove; every root MaterialApp needs it (see legacy_app.dart too).
    return PostHogWidget(
      child: MaterialApp.router(
        title: 'Loanly',
        theme: ThemeData(
          colorSchemeSeed: Colors.indigo,
          useMaterial3: true,
        ),
        routerConfig: _router,
      ),
    );
  }
}
