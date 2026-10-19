# Ticket #4471 — no session replays on the new UI

## Cause
In `posthog_flutter`, mobile session replay is built from screenshots of the
widget tree, and those screenshots are taken by `PostHogWidget`. It has to wrap
the root app widget.

- `lib/legacy_app.dart` (old UI) wraps its `MaterialApp` in `PostHogWidget`,
  so replay works.
- `lib/new_app.dart` (new UI, go_router) returned a bare `MaterialApp.router`
  with no `PostHogWidget`. The SDK is still initialized (`sessionReplay = true`
  in `lib/analytics.dart`), so events, screen views (`PosthogObserver` on the
  router) and taps all arrive. But nothing captures frames, so no recording
  ever shows up. The SDK gives no error or warning when this happens.

The ticket matches this exactly: same SDK and build for both groups, project
settings fine, events present, replays only from the legacy shell.

## Fix
`lib/new_app.dart`: wrapped `MaterialApp.router` in `PostHogWidget`, with a
comment saying why it's there so it doesn't get dropped again. The SDK config,
observers and masking (`maskAllTexts = true`) stay as they were. These are the
only two root app widgets in `lib/`.

## Verify (not done here: no device or PostHog access in this environment)
1. `flutter run --dart-define=NEW_UI=true` on a real device or emulator.
2. Go through calculator → apply → offers, then put the app in the background
   so it flushes.
3. Within a few minutes the session should appear under PostHog → Session
   replay, showing the screens (texts masked) and not just an event timeline.

The fix only reaches users after a new store release. Sessions from builds
that already shipped will stay without replays.
