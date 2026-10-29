import 'package:flutter/material.dart';
import 'package:posthog_flutter/posthog_flutter.dart';

import 'analytics.dart';
import 'screens/offer_screen.dart';
import 'screens/registration_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Analytics.init();
  runApp(const KreditoApp());
}

class KreditoApp extends StatelessWidget {
  const KreditoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return PostHogWidget(
      child: MaterialApp(
        title: 'Kredito',
        theme: ThemeData(colorSchemeSeed: Colors.green, useMaterial3: true),
        navigatorObservers: [PosthogObserver()],
        routes: {
          '/': (_) => const RegistrationScreen(),
          '/offers': (_) => const OfferScreen(),
        },
      ),
    );
  }
}
