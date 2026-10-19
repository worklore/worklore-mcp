# Ticket #4471

The redesign removed `PostHogWidget` from the app's widget tree. The old UI wraps its `MaterialApp` with that widget; the new UI used only `PosthogObserver` with `GoRouter`. The observer tracks navigation, and `Posthog().capture` still sends events, but neither installs the widget hook needed for Flutter session replay. This is why users on the new UI have events but no recordings, despite the shared replay configuration and project settings.

Fixed `NewApp` by wrapping `MaterialApp.router` in `PostHogWidget`, matching the old shell while keeping its existing `GoRouter` observer. New sessions on a build containing this change should be eligible for replay; recordings missing from past sessions cannot be recovered.

Verification: formatting and diff checks pass. A live replay check still requires an iOS or Android run with a valid PostHog project key; this repository uses a CI placeholder key.
