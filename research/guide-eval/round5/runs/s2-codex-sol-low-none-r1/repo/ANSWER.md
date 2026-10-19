# Ticket #4471

The redesigned shell omitted `PostHogWidget`. `PosthogObserver` in its
`GoRouter` records navigation, and `Posthog().capture` still sends events, but
neither provides the widget-tree integration used by Flutter session replay.
The legacy shell includes `PostHogWidget`, which explains why its sessions
have recordings despite both groups sharing the same PostHog configuration.

Wrapped `MaterialApp.router` in `PostHogWidget` in `lib/new_app.dart`, matching
the legacy shell. The existing observer remains in place for screen tracking.

Verification: `dart format` and `git diff --check` pass. A runtime replay check requires
running the new UI on iOS or Android with a valid PostHog key, then confirming
that its session appears in the Replay tab. No app runtime or PostHog project
was available for that check here.
