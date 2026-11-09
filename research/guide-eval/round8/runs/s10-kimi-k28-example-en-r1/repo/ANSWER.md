# Analytics events implementation

Implemented the six events from `docs/EVENTS.md` on the registration and
offers screens via the existing `Analytics.capture` wrapper
(`lib/analytics.dart`). No event names or properties were changed from the
spec; no PII (email, phone) is sent.

## Changes

`lib/screens/registration_screen.dart`
- `registration_email_started` — fires once per screen visit, on the first
  keystroke in the email field. A `bool _emailInputFired` flag on the screen
  state gates it; after that, `onChanged` only triggers `setState` as before.
- `registration_phone_started` — same pattern with `_phoneInputFired` on the
  phone field.
- `loan_amount_changed` — moved out of `onChanged` (which fires on every drag
  step) into `onChangeEnd`, so it fires once per drag. It fires only when the
  value actually changed during that interaction: `onChangeStart` records the
  starting value and `onChangeEnd` compares before capturing
  `{'amount': v.round()}` (int, as specced).
- `terms_accepted` — captured in the checkbox `onChanged` only on the
  false → true transition, so unticking emits nothing.
- `registration_continue_tapped` — captured in the Continue button's
  `onPressed` (the button is only enabled when `_canContinue`), with
  `{'amount': _amount.round() (int), 'terms': _terms (bool)}`, fired before
  navigating to `/offers`.

`lib/screens/offer_screen.dart`
- `offers_scrolled` — a `NotificationListener<ScrollEndNotification>` wraps
  the offers `ListView` and captures `{'offset': notification.metrics.pixels}`
  (double) once per scroll gesture, when the user stops scrolling — not on
  every scroll update.

## Colleague's note — what applied

Applied directly:
- **Text fields: once-per-visit flag in front of the capture in `onChanged`**
  (their step 2). Without this, each email would have produced ~20 events.
- **Sliders: capture in `onChangeEnd`, `onChanged` for UI only** (their step 5).
- **Scrolls: capture from `ScrollEndNotification`, never from scroll-update
  handlers** (their step 6).
- **Keep event names and properties unchanged** (their step 7) — the spec
  says dashboards and funnels already exist on these exact names.

Adapted:
- The spec's "user moved the loan amount slider" only makes sense if the
  value actually moved, so on top of `onChangeEnd` I compare against the
  value at `onChangeStart` and skip a no-op tap-drag.

Not applicable / ignored:
- **Focus-lost / final-value capture** (their step 4): no event here needs a
  field's final value, and the spec forbids sending the values themselves
  (PII), so nothing was moved to a `FocusNode` listener.
- **Their diagnostic "check if this applies" grep and PostHog debug
  verification**: this codebase had zero capture calls before this change —
  it was a fresh implementation, not a fix of an existing event storm, and
  the PostHog key is a CI placeholder, so no live verification was possible.

## Verification

`flutter analyze` / `dart analyze` could not run: the sandbox blocks
executing the Flutter SDK binaries (`Operation not permitted`). I verified
the change by manual review of both files instead — callback signatures,
event names, and property types (`int` amount, `bool` terms, `double`
offset) all match the spec. Worth a quick `flutter analyze` on a machine
where the SDK can execute.
