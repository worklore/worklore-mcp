# PostHog replay missing from the new UI

The redesigned `NewApp` returned `MaterialApp.router` without a surrounding
`PostHogWidget`. Flutter session replay captures frames through that widget.
The SDK could still send events and route information, but the new UI supplied
no screen frames for a replay. The old `LegacyApp` already had the wrapper,
which explains why its sessions appeared in PostHog.

`lib/new_app.dart` now wraps `MaterialApp.router` in `PostHogWidget` and has a
comment explaining why it must stay. The existing `PosthogObserver` remains on
the GoRouter, and `config.sessionReplay = true` remains before SDK setup.

Local verification: Dart formatting passed and `flutter analyze --no-pub`
reported no issues after dependencies were resolved in a local cache.
End-to-end replay verification still requires an iOS or Android device or
emulator and a configured PostHog project: open several screens, background the
app to flush, and check that Session Replay shows screen frames rather than
just an event timeline.
