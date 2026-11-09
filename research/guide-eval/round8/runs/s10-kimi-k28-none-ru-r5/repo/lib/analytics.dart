import 'package:posthog_flutter/posthog_flutter.dart';

/// Thin wrapper around PostHog so the key and host live in one place.
class Analytics {
  static Future<void> init() async {
    final config = PostHogConfig('phc_REPLACE_ME_IN_CI');
    config.host = 'https://eu.i.posthog.com';
    config.captureApplicationLifecycleEvents = true;
    await Posthog().setup(config);
  }

  /// Sends one event. [props] is optional.
  static Future<void> capture(String event, [Map<String, Object>? props]) =>
      Posthog().capture(eventName: event, properties: props);
}
