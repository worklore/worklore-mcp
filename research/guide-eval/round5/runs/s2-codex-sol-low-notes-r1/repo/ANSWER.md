# Ticket #4471

The new UI's `MaterialApp.router` was missing `PostHogWidget`. Flutter session replay uses that widget to capture frames. The legacy shell wraps its `MaterialApp`, so its recordings appear; the new shell still sends events through the shared PostHog setup and router observer, but produces no replay frames. The project recording settings and SDK version are shared between both groups and do not explain the difference.

I wrapped `MaterialApp.router` in `PostHogWidget` in `lib/new_app.dart` and added a comment explaining why the wrapper must stay. The existing `sessionReplay = true` setup and `PosthogObserver` remain in place.

Verification: `git diff --check` passes. `flutter analyze --no-pub` cannot resolve Flutter and package imports because this checkout has no `.dart_tool` package configuration; dependencies were not fetched. Replay itself requires a device or emulator and a PostHog recording after the changed build runs, so it was not verified here.
