# Ticket #4471 — no session replays on the new UI

## Cause
On mobile, `posthog_flutter` builds session replay from screenshots of the
widget tree, and those screenshots are taken by `PostHogWidget`. Only the
legacy shell (`lib/legacy_app.dart`) wraps its `MaterialApp` in
`PostHogWidget`. The redesigned shell (`lib/new_app.dart`, default since
2.3.0, selected by `NEW_UI=true`) returns a bare `MaterialApp.router`.

So for new-UI users the SDK is set up the same way (`sessionReplay = true` in
`lib/analytics.dart`, same version, same build): events, taps and screen views
(via `PosthogObserver` on the GoRouter) all arrive, but no frames are captured,
so a recording never shows up. The SDK doesn't report an error or warning when
this happens. That fits the ticket exactly: same build, events fine, replays
only from the A/B group on `LegacyApp`.

Project settings (record on, 100% sampling, min duration 0) were not the problem.

## Fix
- `lib/new_app.dart`: wrapped `MaterialApp.router` in `PostHogWidget(...)`,
  with a comment explaining why it's required.
- `lib/legacy_app.dart`: added a comment on the existing wrapper so it isn't
  removed.

The rest was already correct: `config.sessionReplay = true` is set before
`Posthog().setup(config)`, `PosthogObserver` is on both the GoRouter and the
legacy navigator, and `maskAllTexts = true` masks PII.

## Verification
`flutter analyze` passes with no issues. I didn't run the app on a device and
nothing was deployed. To verify on a device: `flutter run --dart-define=NEW_UI=true` on a real
device or emulator, go through calculator → apply → offers, then put the app
in the background so it flushes. Within a few minutes the session should
appear in PostHog → Session replay with frames, not just an event timeline.
Users get the fix only after the next store release.

## Note for the future
Any new root app widget (flavor, white-label build, another redesign) needs
its own `PostHogWidget`. Replay works only in shells that have the wrapper.
