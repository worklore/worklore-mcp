# Ticket #4471: no session replays on the new UI

## Why

Replay on mobile is built from screenshots of the widget tree. The SDK takes
those screenshots inside `PostHogWidget`: its state owns the
`ScreenshotCapturer` and the `NativeCommunicator` that sends frames to the
native side (`posthog_flutter` 5.55.0, `lib/src/posthog_widget.dart`).

- `LegacyApp` (`lib/legacy_app.dart`) wraps its `MaterialApp` in
  `PostHogWidget`. Its sessions record. This is the A/B group the ticket says
  works.
- `NewApp` (`lib/new_app.dart`) returned a bare `MaterialApp.router` with no
  wrapper. Events, screen tracking (`PosthogObserver` on the GoRouter) and taps
  all still go out, so the Events tab looks healthy. There are simply no frames
  to record, so the Replay tab stays empty for these users.

Nothing in the PostHog project settings or `config.sessionReplay = true` is
involved. Both shells share `Analytics.init()` and the same SDK version. The
only difference between the two groups is the wrapper.

## Fix

`lib/new_app.dart`: wrapped `MaterialApp.router` in `PostHogWidget`, the same
way `LegacyApp` does. Added a comment in both shells saying the wrapper is
needed for replay, so it is not removed later.

## Verification

- `flutter analyze`: no issues (run against the changed code).
- Not done: a run on a device or emulator, and checking a real session in
  PostHog. Nothing was deployed or submitted anywhere. To confirm, run
  `flutter run --dart-define=NEW_UI=true` on a device, move through a few
  screens, background the app, and check that a new session appears in
  Session replay with screenshots.

## Checklist for other shells

Each production root widget (`MaterialApp`, `MaterialApp.router`,
`CupertinoApp`) must sit inside a `PostHogWidget`. Right now that is both
`LegacyApp` and `NewApp`. `grep -rn "MaterialApp\|PostHogWidget" lib/` shows
them.
