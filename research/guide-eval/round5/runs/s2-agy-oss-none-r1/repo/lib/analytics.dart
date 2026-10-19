import 'package:posthog_flutter/posthog_flutter.dart';

class Analytics {
  static Future<void> init() async {
    final config = PostHogConfig('phc_REPLACE_ME_IN_CI');
    config.host = 'https://eu.i.posthog.com';
    config.captureApplicationLifecycleEvents = true;
    config.sessionReplay = true;
    config.sessionReplayConfig.maskAllTexts = true;
    config.sessionReplayConfig.maskAllImages = false;
    await Posthog().setup(config);
  }

  static Future<void> track(String event, [Map<String, Object>? props]) =>
      Posthog().capture(eventName: event, properties: props);
}
