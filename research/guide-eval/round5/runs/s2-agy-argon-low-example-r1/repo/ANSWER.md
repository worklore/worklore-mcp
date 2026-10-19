# Ticket #4471 Resolution: Empty PostHog Session Replays on New UI

## Root Cause (Why)
On mobile in Flutter (`posthog_flutter`), PostHog session replay captures frames by taking screenshots of the widget tree via `PostHogWidget`. Without `PostHogWidget` wrapping the root app widget, the SDK continues to capture events, taps, and screen views (via `PosthogObserver`), but has no visual frames to send—resulting in empty/missing session recordings without throwing errors or warnings.

In this project:
- **Old UI (`lib/legacy_app.dart`)**: `LegacyApp` wraps its `MaterialApp` inside `PostHogWidget`, so session replay works properly.
- **New UI (`lib/new_app.dart`)**: When `NewApp` was created using `MaterialApp.router` and `go_router`, `PosthogObserver()` was added to the router, and `posthog_flutter` was imported, but `MaterialApp.router` was **not** wrapped in `PostHogWidget`.

## Fix
- Wrapped `MaterialApp.router` in `lib/new_app.dart` with `PostHogWidget`.
- Added comments in both `lib/new_app.dart` and `lib/legacy_app.dart` explaining that `PostHogWidget` is required for session replay so it is not accidentally removed in future refactors.

## Which Parts of the Colleague's Note Applied

### Applied
- **Core diagnosis & multi-shell explanation**: `PostHogWidget` is required around the root app widget to capture screenshot frames for Flutter session replay, and when adding a second redesigned app shell (`MaterialApp.router` in `lib/new_app.dart`), it is easy to wrap the old shell (`lib/legacy_app.dart`) while forgetting to wrap the new one.
- **"Check if this applies to you" (Steps 1–3)**:
  1. `posthog_flutter` (`^5.36.0`, which is `>= 5.14.0`) is present in `pubspec.yaml`.
  2. `config.sessionReplay = true` is configured in `lib/analytics.dart`.
  3. Checking `MaterialApp` vs. `PostHogWidget` across `lib/` immediately showed `LegacyApp` (`MaterialApp`) had `PostHogWidget`, whereas `NewApp` (`MaterialApp.router`) did not.
- **Fix Step 1 & Step 2**: Finding every root app widget (`MaterialApp` in `lib/legacy_app.dart` and `MaterialApp.router` in `lib/new_app.dart`), wrapping the unwrapped `MaterialApp.router` in `PostHogWidget`, and adding a comment explaining why the wrapper is needed.

### Did Not Apply / Already Satisfied (Ignored for Changes)
- **Fix Step 3 (Enabling session replay / `startSessionRecording()`)**: `config.sessionReplay = true` was already configured prior to `Posthog().setup(config)` in `lib/analytics.dart` (and recording is not gated behind a feature flag/consent flow).
- **Fix Step 4 (`PosthogObserver()`)**: Both `LegacyApp` (`navigatorObservers: [PosthogObserver()]`) and `NewApp` (`GoRouter(observers: [PosthogObserver()], ...)`) already had `PosthogObserver()` configured.
- **Fix Step 5 (`maskAllTexts = true`)**: `config.sessionReplayConfig.maskAllTexts = true` was already set in `lib/analytics.dart`.
- **Device/Emulator live verification**: Running a live build against an external PostHog server is outside the local repository scope and ground rules (no external service reporting/deployment).
