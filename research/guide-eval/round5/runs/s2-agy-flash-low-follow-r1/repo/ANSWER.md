# PostHog Session Replay Issue in New UI

## Cause of the Issue
In Flutter mobile apps, PostHog session replay constructs recordings by taking screenshots of the widget tree. This mechanism requires the root app widget (`MaterialApp`, `MaterialApp.router`, or `CupertinoApp`) to be wrapped in a `PostHogWidget`.

- `LegacyApp` (`lib/legacy_app.dart`) wrapped its `MaterialApp` with `PostHogWidget`, so session recordings worked as expected for users in the old UI cohort.
- When `NewApp` (`lib/new_app.dart`) was introduced for the redesign, its `MaterialApp.router` was returned directly without a `PostHogWidget` wrapper.
- As a result, events and route changes tracked by `PosthogObserver` were still sent to PostHog, but no screenshot frames were captured, causing the session replay to appear empty in the PostHog dashboard for users on the new UI.

## Fix
In [`lib/new_app.dart`](file:///tmp/h-VKIVZw/lib/new_app.dart), `MaterialApp.router` has been wrapped inside `PostHogWidget`:

```dart
@override
Widget build(BuildContext context) {
  // PostHog session replay requires PostHogWidget to capture screenshot frames of the widget tree.
  return PostHogWidget(
    child: MaterialApp.router(
      title: 'Loanly',
      theme: ThemeData(
        colorSchemeSeed: Colors.indigo,
        useMaterial3: true,
      ),
      routerConfig: _router,
    ),
  );
}
```

A clarifying comment was included so the wrapper is not accidentally removed in future refactors.
