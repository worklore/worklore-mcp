# PostHog Session Replay Issue in New UI

## Cause of the Issue
In `posthog_flutter`, capturing session replay snapshots (and mask coordinates) on mobile requires the root widget tree of the application to be wrapped in [`PostHogWidget`](https://posthog.com/docs/session-replay/mobile).

- In [`lib/legacy_app.dart`](file:///tmp/h-VnoQ72/lib/legacy_app.dart), `MaterialApp` was properly wrapped inside `PostHogWidget`:
  ```dart
  return PostHogWidget(
    child: MaterialApp(
      ...
    ),
  );
  ```
- In [`lib/new_app.dart`](file:///tmp/h-VnoQ72/lib/new_app.dart), `NewApp` directly returned `MaterialApp.router(...)` without wrapping it in `PostHogWidget`.

While event capturing and screen navigation tracking functioned because `Analytics.init()` and `PosthogObserver()` were registered, the screenshot capturer and repaint boundary mechanics hosted by `PostHogWidget` were absent in `NewApp`. As a result, no replay frames were produced or dispatched for users running the new UI shell.

## Solution
Updated [`lib/new_app.dart`](file:///tmp/h-VnoQ72/lib/new_app.dart) to wrap `MaterialApp.router(...)` in `PostHogWidget`, matching the configuration in the legacy app shell.
