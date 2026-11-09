# Analytics events implementation

Implemented all six events from `docs/EVENTS.md` via the existing `Analytics`
wrapper (`lib/analytics.dart`). Event names and properties match the spec
exactly, so existing dashboards/funnels keep working. No PII (email, phone
values) is sent as properties.

## Changes

`lib/screens/registration_screen.dart`
- `registration_email_started` — fired in the email `onChanged`, but only on
  the first edit per screen visit, behind a `_emailStartedFired` flag.
- `registration_phone_started` — same pattern with a `_phoneStartedFired`
  flag.
- `loan_amount_changed` — fired in the slider's `onChangeEnd` (once per drag,
  when the user lets go) with `amount: v.round()` (int). `onChanged` still
  only updates the UI.
- `terms_accepted` — fired when the checkbox is ticked (`v == true`). No flag:
  a checkbox toggle is a discrete action, not a continuous stream.
- `registration_continue_tapped` — fired in the Continue button's `onPressed`
  with `amount: _amount.round()` (int) and `terms: _terms` (bool), before
  navigating to `/offers`.

`lib/screens/offer_screen.dart`
- `offers_scrolled` — the ListView is wrapped in a
  `NotificationListener<ScrollEndNotification>`; the event fires when
  scrolling stops with `offset: n.metrics.pixels` (double), not on every
  scroll update.

## Colleague's note — what applied

This project is exactly the case described in the note (Flutter app,
per-event-billed analytics), and I applied these parts:

- **Text fields: fire once per screen visit, on the first edit**, using
  `bool _<field>InputFired` flags in the screen state — applied to
  `registration_email_started` and `registration_phone_started`. A naive
  implementation would have fired on every keystroke.
- **Sliders: move the capture from `onChanged` to `onChangeEnd`** so it fires
  once per drag with the final value — applied to `loan_amount_changed`.
  `onChanged` was kept for UI updates only.
- **Scrolls: listen for `ScrollEndNotification`** rather than scroll-update
  handlers — applied to `offers_scrolled`.
- **Keep event names and properties unchanged** — the spec's names and
  property types (`amount` int, `terms` bool, `offset` double) are used
  verbatim.
- The PII ground rule also aligns with the spec note: no email/phone values
  are attached to any event.

Parts I did not apply (not relevant here):
- FocusNode/focus-lost handlers — no event needed the field's final value, so
  the once-per-visit flag was enough for the text fields.
- The "reproduce/debug" steps (`PostHogConfig.debug`, dashboard checks) — left
  as a manual verification step; nothing was sent to any external service.

## Verification

I could not run `flutter analyze` or a debug build in this environment
(the toolchain binaries are present but not permitted to execute), so the
change was verified by code review: all six events from the spec are wired,
property types match the table (`amount` int via `.round()`, `offset` double
via `metrics.pixels`), and captures behind continuous callbacks
(`onChanged`, scroll updates) are guarded by the patterns above.
