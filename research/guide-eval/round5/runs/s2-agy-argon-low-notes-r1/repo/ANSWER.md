# Why Session Replay Was Empty on the New UI

## Root Cause
On Flutter, PostHog session replay works by capturing screenshots of the widget tree via `PostHogWidget`. Without `PostHogWidget` wrapping the root app widget (`MaterialApp` / `MaterialApp.router`), the `posthog_flutter` SDK continues to capture standard analytics events, screen transitions (via `PosthogObserver`), and user interactions, but has no visual frames to record and upload—resulting in missing/empty session replays without emitting any errors or warnings.

In `lib/legacy_app.dart`, `MaterialApp` was wrapped in `PostHogWidget`:
```dart
return PostHogWidget(
  child: MaterialApp(
    ...
  ),
);
```

However, when the redesigned shell was created in `lib/new_app.dart`, `MaterialApp.router` was returned directly without the `PostHogWidget` wrapper, even though `posthog_flutter` was imported and `PosthogObserver()` was attached to `GoRouter`.

## Fix
Wrapped `MaterialApp.router` in `lib/new_app.dart` with `PostHogWidget` (matching `LegacyApp`) and added a comment explaining that `PostHogWidget` is required for session replay.
