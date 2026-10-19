# Root Cause & Fix for Ticket #4471 (Empty Session Replays on New UI)

## Why Session Replay Was Empty on the New UI

On Flutter mobile, PostHog session replay works by capturing screenshots of the widget tree using `PostHogWidget`. Without `PostHogWidget` wrapping the root app widget (`MaterialApp` / `MaterialApp.router`), the `posthog_flutter` SDK still captures and sends lifecycle events, screen views (via `PosthogObserver`), and custom events, but it has no visual frames to record—resulting in empty/missing session replays without emitting any errors or warnings.

- **Old UI (`lib/legacy_app.dart`)**: `LegacyApp` wrapped its `MaterialApp` inside `PostHogWidget`, so session replays worked as expected.
- **New UI (`lib/new_app.dart`)**: When `NewApp` was introduced with `MaterialApp.router`, `PostHogWidget` was omitted around `MaterialApp.router`.

## Fix Applied

1. Wrapped `MaterialApp.router` in `lib/new_app.dart` with `PostHogWidget`.
2. Added comments in both `lib/new_app.dart` and `lib/legacy_app.dart` explaining that `PostHogWidget` is required for PostHog session replay so it is not accidentally removed in future refactors.
