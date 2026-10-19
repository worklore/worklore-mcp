# Why Session Replay Was Empty on the New UI

## Root Cause

In Flutter (`posthog_flutter`), mobile session replay is built from screenshots of the widget tree captured by `PostHogWidget`. If the active `MaterialApp` / `MaterialApp.router` is not wrapped in `PostHogWidget`, the SDK still records analytics events, taps, and screen views (via `PosthogObserver`) without logging any error or warning, but it captures no frames—resulting in empty/missing session replays in PostHog.

The app ships two root shells selected in `lib/main.dart` via the `NEW_UI` compile-time flag:

- **Old UI (`LegacyApp` in `lib/legacy_app.dart`)**: Wrapped its `MaterialApp` in `PostHogWidget`, so session replays recorded normally for the `NEW_UI=false` A/B group.
- **New UI (`NewApp` in `lib/new_app.dart`)**: Configured `PosthogObserver()` on its `GoRouter` and shared `Analytics.init()` (`config.sessionReplay = true` in `lib/analytics.dart`), but returned `MaterialApp.router` directly **without** a `PostHogWidget` wrapper.

## Fix

1. Wrapped `MaterialApp.router` with `PostHogWidget` in `NewApp.build` (`lib/new_app.dart`).
2. Added comments on the `PostHogWidget` wrappers in `lib/new_app.dart` and `lib/legacy_app.dart` explaining that `PostHogWidget` is required for session replay so it is not inadvertently removed later.
3. Verified the remaining session replay requirements:
   - `config.sessionReplay = true` and `config.sessionReplayConfig.maskAllTexts = true` are set before `Posthog().setup(config)` in `lib/analytics.dart`.
   - `PosthogObserver()` remains registered in `GoRouter.observers` (`lib/new_app.dart`) and `MaterialApp.navigatorObservers` (`lib/legacy_app.dart`).
