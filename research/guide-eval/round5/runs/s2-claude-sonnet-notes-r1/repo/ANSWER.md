# Ticket #4471: empty replays on the new UI

**Cause:** On mobile, `posthog_flutter` builds replays from screenshots taken through `PostHogWidget`. `LegacyApp` wraps its `MaterialApp` in `PostHogWidget`. `NewApp` (`lib/new_app.dart`) returns a bare `MaterialApp.router`, so the redesign dropped the wrapper. `Analytics.init()` still sets `sessionReplay = true` and `PosthogObserver` is still on the router. That is why events and screen views arrive but there is no recording. Project settings were never the problem.

**Fix:** Wrapped `MaterialApp.router` in `PostHogWidget` in `lib/new_app.dart`, with a comment so it isn't removed later.

**Not verified:** I didn't run the app, and `flutter analyze` and the tests weren't run. To check, build on a device or emulator, click through a few screens, background the app, and look in the Replay tab after a few minutes. Nothing was deployed.

**Note:** With `maskAllTexts = true`, text will appear masked in replays. That is intended.
