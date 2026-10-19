# Ticket #4471: no session replays on the new UI

## Cause

On Flutter, `posthog_flutter` doesn't record the screen natively. The
`PostHogWidget` widget makes the recording: it watches for frame changes,
takes screenshots of the widget tree under it, applies masking, and sends the
snapshots to the native SDK. `config.sessionReplay = true` only switches the
feature on. If no `PostHogWidget` is in the tree, nothing gets recorded.

- `lib/legacy_app.dart` wraps `MaterialApp` in `PostHogWidget`, so replays work.
- `lib/new_app.dart` (the redesign, which moved to `MaterialApp.router` +
  go_router) dropped the wrapper. Only the `PosthogObserver` was carried over.

That fits every symptom in the ticket. Events and `$screen` come from
`Posthog().capture` and `PosthogObserver`, which don't need the widget, so they
still arrive. Same SDK version, same build, project settings fine: the only
difference between the two groups is which root widget runs.

## Fix

`lib/new_app.dart`: wrap `MaterialApp.router` in `PostHogWidget`, the same way
the legacy shell does. It sits above the router, so every go_router screen
(including `/offers`) is captured. The `maskAllTexts` setting from
`analytics.dart` applies unchanged.

`flutter analyze`: no issues. I haven't run it on a device. To check: build
with `--dart-define=NEW_UI=true`, use the app for a few seconds, and confirm a
recording shows up in the Replay tab.

## Unrelated thing I noticed (not changed)

`CalculatorScreen`'s Apply button calls `Navigator.of(context).pushNamed('/apply')`.
Under go_router there is no named-route table, so in the new UI this most
likely throws instead of navigating (`context.push('/apply')` would work there).
It's worth checking separately: if the button really is broken, it could also
be hurting the new UI's funnel numbers in the A/B test.
