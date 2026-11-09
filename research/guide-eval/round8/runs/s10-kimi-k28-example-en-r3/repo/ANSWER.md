# ANSWER

## What was implemented

All six events from `docs/EVENTS.md`, via the existing `Analytics` wrapper
(`lib/analytics.dart`). Names and properties match the spec exactly; no PII
(email/phone values) is sent anywhere.

### `lib/screens/registration_screen.dart`

- `registration_email_started` — fired on the first keystroke in the email
  field only, guarded by a `_emailStartedFired` flag. `onChanged` still calls
  `setState` on every keystroke for the Continue-button validation, but the
  event fires once.
- `registration_phone_started` — same pattern with a `_phoneStartedFired`
  flag.
- `loan_amount_changed` — capture moved out of the slider's `onChanged`
  (which runs on every step of a drag) into `onChangeEnd`, so it fires once
  per drag with the final value: `{'amount': v.round()}` (int, per spec).
- `terms_accepted` — fired in the checkbox `onChanged` when the value becomes
  `true` (i.e. on each tick, not on untick).
- `registration_continue_tapped` — fired in the Continue button's `onPressed`
  with `{'amount': _amount.round(), 'terms': _terms}` before navigating.

### `lib/screens/offer_screen.dart`

- `offers_scrolled` — the screen is now stateful; the `ListView` is wrapped
  in a `NotificationListener<ScrollEndNotification>` that fires the event once
  per screen visit with `{'offset': n.metrics.pixels}` (double, scroll
  position where the user stopped). It never fires from scroll updates.

## Which parts of the colleague's note applied

Applied directly:

- **Text fields: once-per-visit flag on first edit.** The note's core warning
  (an event per keystroke exhausts a per-event quota) is exactly the risk
  here, since the spec's "user started typing" events would otherwise sit in
  `onChanged` and fire per keystroke. No final-value property is needed for
  these fields, so the note's focus-lost variant was not needed (and would
  have been wrong: the values are PII and must not be sent).
- **Slider: capture in `onChangeEnd`, keep `onChanged` for UI only.**
  `loan_amount_changed` carries the chosen amount, and `onChangeEnd` is where
  that value is final.
- **Scrolls: `ScrollEndNotification`, never scroll-update handlers.** Applied
  to `offers_scrolled`.
- **Keep event names and properties unchanged** so the existing dashboards
  and funnels keep working — done.
- **Flag placement on long-lived state.** The note says to decide whether
  "once" means per visit or per flow when the state object survives
  navigation. The registration screen's state survives the trip to `/offers`
  and back, so I treated "once" as once per registration flow (going back
  from offers does not re-fire email/phone started). A fresh visit to
  `/offers` creates a new state object, so `offers_scrolled` re-arms per
  visit.

Extended beyond the note:

- The note prescribes `ScrollEndNotification` for scrolls but not a
  once-only flag; a user who scrolls-starts-stops several times would still
  emit several events per visit, which pollutes a funnel step on a
  per-event-billed plan. I added a once-per-visit flag on top, by the same
  reasoning the note applies to text fields.

Did not apply:

- The note's diagnostic grep (`onChanged` / controller listeners /
  scroll-update handlers already containing capture calls): nothing fired
  events yet, so there was nothing to find — the note's value here was
  forward-looking, as the "how to wire the spec without blowing the quota"
  playbook.
- Debounce: unnecessary once the once-only flags are in place.
- `FocusNode` tap/focus capture: the spec has no tap/focus event.
- Debug-build verification with `PostHogConfig.debug = true`: could not run
  (see below).

## Verification

- `dart format --set-exit-if-changed lib/` passes (canonical formatting,
  which also confirms both files parse).
- `flutter analyze` / `flutter pub get` could not be run: the local Flutter
  tool binary is blocked by macOS ("Operation not permitted"), and standalone
  `dart pub get` cannot resolve `sdk: flutter` dependencies, so package
  resolution and full static analysis were unavailable in this environment.
  Please run `flutter pub get && flutter analyze` (and the debug-keystroke
  check from the note) where the Flutter tool is usable.

No files were created besides the two edited screens and this ANSWER.md.
