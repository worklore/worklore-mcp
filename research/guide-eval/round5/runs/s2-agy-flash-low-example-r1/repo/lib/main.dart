import 'package:flutter/material.dart';

import 'analytics.dart';
import 'legacy_app.dart';
import 'new_app.dart';

const bool useNewUi = bool.fromEnvironment('NEW_UI', defaultValue: true);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Analytics.init();
  runApp(useNewUi ? const NewApp() : const LegacyApp());
}
