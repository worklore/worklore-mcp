# Ticket #4471: new UI session replay

## Cause

`main.dart` initializes PostHog before choosing either UI shell. Replay is enabled in `analytics.dart`, and both shells have `PosthogObserver` for screen events. The legacy shell wraps its `MaterialApp` in `PostHogWidget`, but the new shell returned `MaterialApp.router` directly. Flutter session replay needs that wrapper to capture widget frames. This explains why new UI events and taps arrived while its replay recordings were absent.

## Fix

Wrapped the new UI's `MaterialApp.router` in `PostHogWidget` in `lib/new_app.dart`, with a comment explaining why it must remain. The existing replay setting, text masking, and router observer remain in place.

## Colleague's note

The applicable part was the second app shell example: each production app shell needs `PostHogWidget` around its root app widget. The note's checks for an installed SDK, enabled replay, and a route observer also applied and were already satisfied here. Its suggested `startSessionRecording()` path does not apply because `config.sessionReplay = true` starts recording during setup. Changing PostHog project settings, sampling, or minimum duration does not address this ticket; the ticket says they are already enabled or permissive. The optional masking suggestion was already implemented with `maskAllTexts = true`.

## Verification

Static code inspection confirms both UI shells now wrap their root app widget and the new router still has `PosthogObserver`. `flutter analyze` completed with no issues. A device replay check is still needed after shipping: run the new UI on iOS or Android with a real PostHog token, navigate through several screens, background the app, and confirm a playable recording appears in PostHog Session Replay. This checkout has no iOS or Android project, so it cannot perform that device check here.

Reference: [PostHog Flutter session replay installation](https://posthog.com/docs/session-replay/installation/flutter).
