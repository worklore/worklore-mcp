# Root Cause & Fix for Ticket #4471

## Why Session Replay Was Empty on the New UI

In `posthog_flutter`, session replay relies on `PostHogWidget` wrapping the root application widget (`MaterialApp` or `MaterialApp.router`). `PostHogWidget` provides the `RepaintBoundary` and screenshot/DOM-like widget tree capture required to record and send session replay snapshots (`$snapshot` events) to PostHog.

- **Old UI (`lib/legacy_app.dart`)**: Wrapped `MaterialApp` in `PostHogWidget(child: MaterialApp(...))`, so both events and session replay recordings worked properly.
- **New UI (`lib/new_app.dart`)**: Configured `PosthogObserver()` on `GoRouter` (which allowed screen events and custom `Analytics.track` events to arrive), but omitted the `PostHogWidget` wrapper around `MaterialApp.router`. Without `PostHogWidget`, no screen recordings were captured for users on the new UI.

Also note: in `lib/screens/calculator_screen.dart`, the "Apply" button used `Navigator.of(context).pushNamed('/apply')`, whereas `NewApp` uses `GoRouter` (`MaterialApp.router`), where `PostHogWidget` wraps the router app shell.

## Fix

Wrapped `MaterialApp.router` inside `PostHogWidget` in `lib/new_app.dart` (matching `lib/legacy_app.dart`).
