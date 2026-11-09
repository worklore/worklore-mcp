# Analytics events implementation

Implemented the six events from `docs/EVENTS.md` on the registration and
offers screens via the existing `Analytics.capture` wrapper
(`lib/analytics.dart`). Event names and properties match the spec exactly;
no PII (email/phone values) is sent; screen views were left to the existing
`PosthogObserver`.

## Registration screen (`lib/screens/registration_screen.dart`)

- `registration_email_started` — fired in the email field's `onChanged`,
  but only on the first keystroke of each screen visit, guarded by a
  `_emailStartedFired` flag. No properties.
- `registration_phone_started` — same pattern, `_phoneStartedFired` flag.
  No properties.
- `loan_amount_changed` — fired in the slider's `onChangeEnd` (once per
  drag, when the user lets go) with `amount` (int, `v.round()`). `onChanged`
  still only updates the UI.
- `terms_accepted` — fired when the checkbox is ticked (`v == true`). A tap
  is a single deliberate action, so no flag needed. No properties.
- `registration_continue_tapped` — fired in the Continue button with
  `amount` (int) and `terms` (bool), before navigating to `/offers`.

## Offers screen (`lib/screens/offer_screen.dart`)

- `offers_scrolled` — the `ListView.builder` is wrapped in a
  `NotificationListener<ScrollEndNotification>` that fires once per
  completed scroll with `offset` (double, `notification.metrics.pixels`).
  The listener returns `false` so the notification keeps propagating.

## Verification

Could not run `flutter analyze` or a build: the Flutter SDK on this machine
(`/Users/valentinakoniukhova/development/flutter`) is not executable from
this shell (macOS "Operation not permitted"), and the project has no
`.dart_tool`. Both modified files were re-read and checked manually against
the spec (exact event names, property types `amount: int`, `terms: bool`,
`offset: double`) and against the Material API (`Slider.onChangeEnd`,
`ScrollEndNotification.metrics.pixels`).

## Which parts of the colleague's note applied

This codebase is exactly the case the note describes, so most of it
applied:

- **Text fields fire once per visit behind a flag** (`bool
  _<field>InputFired` on the screen state) — applied to email and phone.
  Without it, `onChanged` would send one event per keystroke.
- **Sliders: move the capture from `onChanged` to `onChangeEnd`** —
  applied to `loan_amount_changed`, which also legitimately needs the final
  value (`amount`), as the note allows for non-sensitive final values.
- **Scrolls: `ScrollEndNotification`, never scroll-update handlers** —
  applied to `offers_scrolled`.
- **Keep event names and properties unchanged** — followed; nothing was
  renamed.
- **Do not send PII as properties** — followed; email/phone values are never
  captured.

Parts that did not apply:

- **FocusNode / focus-lost handlers** — not needed; no event required a
  field's final value (only the slider's, which `onChangeEnd` covers).
- **The reproduce/verify section with `PostHogConfig.debug`** — could not
  run a debug build for the same OS-permission reason as above.
- The pricing/quota framing itself wasn't the goal here; the value was the
  firing-discipline guidance, which shaped the three `onChanged` and the
  scroll event placement.
