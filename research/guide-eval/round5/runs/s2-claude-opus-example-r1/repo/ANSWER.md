# Ticket #4471: no session replays on the new UI

## Cause
Replay in `posthog_flutter` on mobile is built from screenshots of the widget
tree, and those screenshots are taken by `PostHogWidget`. The app has two root
widgets, chosen in `lib/main.dart` by `NEW_UI`:

- `LegacyApp` (`lib/legacy_app.dart`) wraps its `MaterialApp` in `PostHogWidget`,
  so replays work.
- `NewApp` (`lib/new_app.dart`) returned a bare `MaterialApp.router` with no
  `PostHogWidget`. The SDK was initialized the same way (`sessionReplay = true`
  in `lib/analytics.dart`) and `PosthogObserver` was on the GoRouter, so events
  and screens arrived. But no frames were captured, so the new-UI users got no
  recordings. The SDK gives no error or warning when this happens.

This explains why it splits by UI and not by SDK version or project settings:
same build, same config, the only difference is the wrapper.

## Fix
- `lib/new_app.dart`: wrapped `MaterialApp.router` in `PostHogWidget`, with a
  comment saying why it's there.
- `lib/legacy_app.dart`: added the same comment to the existing wrapper so
  neither one gets removed by accident.

Nothing else needed to change. `sessionReplay = true` is set before `setup()`,
and `PosthogObserver` is already in the GoRouter `observers`.

## Verification
- `flutter pub get` and `flutter analyze` ran with no issues found. Not run on
  a device or emulator here, and no real replay was checked in PostHog.
- To verify on a device or emulator: `flutter run --dart-define=NEW_UI=true`,
  go Calculator → Apply → Offers, then put the app in the background so it
  flushes. Within a few minutes the session should show up under Session replay
  with real frames, not an empty player. Replays only reach users after the
  next store release.

## Which parts of the colleague's note applied
- **Applied:** the core diagnosis (no `PostHogWidget` means events but no
  replay, and nothing in the logs). So did the "more than one `MaterialApp`"
  warning: this is exactly the redesign/second-shell case, where the old shell
  had the wrapper and the new one didn't. Also applied: wrapping each root app
  widget, adding a "why" comment, and their verify steps.
- **Already in place here, no change needed:** `sessionReplay = true` before
  setup, `PosthogObserver` (here on GoRouter `observers`), and
  `maskAllTexts = true`.
- **Didn't apply:** the feature-flag `startSessionRecording()` path (this app
  doesn't gate replay), the trial-and-error with console settings (the ticket
  already confirms recording is on, sampling is 100% and minimum duration is 0),
  and the web/posthog-js remark (this app is iOS + Android only).
