# Analytics events on registration and offers screens

Implemented the six events in `docs/EVENTS.md` using the existing `Analytics.capture` wrapper. Only `lib/screens/registration_screen.dart` and `lib/screens/offer_screen.dart` changed.

## What was done

| Event | Where | Trigger | Properties |
|---|---|---|---|
| `registration_email_started` | registration | First non-empty input in the Email field, once per screen visit | none |
| `registration_phone_started` | registration | First non-empty input in the Phone field, once per screen visit | none |
| `loan_amount_changed` | registration | Slider `onChanged` | `amount` (int, rounded) |
| `terms_accepted` | registration | Checkbox ticked (not when unticked) | none |
| `registration_continue_tapped` | registration | Continue pressed, before navigating to `/offers` | `amount` (int), `terms` (bool) |
| `offers_scrolled` | offers | End of a scroll gesture (`ScrollEndNotification`) | `offset` (double, `metrics.pixels`) |

Email and phone values are never sent, per the PII note in the spec.

## Implementation choices

- **"Started" events fire once per visit.** The text fields call `onChanged` on every keystroke, so each field has a `_xxxStarted` flag that is set on the first non-empty change. The flags live in the State, so returning to the screen counts as a new visit.
- **`loan_amount_changed` fires on every slider change.** `Slider.onChanged` fires for each of the 49 divisions while dragging. That matches "moved the slider" in the spec, but it can produce many events per drag. If the dashboards are too noisy, switch to `onChangeEnd`.
- **`offers_scrolled` uses `ScrollEndNotification`** wrapped around the existing `ListView`, not `ScrollController` listeners. This gives one event per scroll, with the final offset. `OfferScreen` stays a `StatelessWidget`. Using `ScrollUpdateNotification` would fire on every frame.
- **Continue handler.** The Continue button's inline closure became `_onContinue()` so the event and navigation sit together. The `terms` value is read from state. The button is only enabled when terms are accepted, so it is always `true` at that point.
- Events go through `Analytics.capture`, as the README requires. No new wrapper or key handling was added.

## Verification

- `flutter analyze`: **No issues found.**
- `dart format --set-exit-if-changed` on both files: **0 files changed.**
- Not run: a device or simulator run, so the events have not been seen arriving in PostHog. Nothing was sent to any external service.

## Side effects I cleaned up

Running `flutter pub get` to make the analyzer work also:
- rewrote `analysis_options.yaml` to add an `analyzer.exclude` block. I reverted it with `git checkout`.
- created `.dart_tool/` and `pubspec.lock`. I deleted both. They were not in the repo before I started.

The final working-tree changes are only the two screen files and this `ANSWER.md`.

## Not done / open for product

- The `phc_REPLACE_ME_IN_CI` key in `lib/analytics.dart` is still a placeholder. Events will not reach PostHog until CI injects the real key. I did not touch it.
- The spec does not define `offers_scrolled` precisely ("how far they scrolled"). I took it as the offset at the end of each scroll. If product wants a different measure, it is a one-line change in `offer_screen.dart`.
