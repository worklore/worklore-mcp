# Analytics events

Implemented all events from `docs/EVENTS.md` using the existing `Analytics.capture` wrapper.

- `lib/screens/registration_screen.dart`
  - Sends `registration_email_started` and `registration_phone_started` once per field when the user first enters non-empty text.
  - Sends `loan_amount_changed` with the rounded integer `amount` whenever the slider changes.
  - Sends `terms_accepted` only when the checkbox becomes checked.
  - Sends `registration_continue_tapped` with the current integer `amount` and boolean `terms` before opening the offers screen.
  - Does not send email addresses or phone numbers.
- `lib/screens/offer_screen.dart`
  - Listens for offer-list scroll updates and sends `offers_scrolled` with the current double `offset` in pixels.

Verification: `git diff --check` passes. Flutter analysis and runtime checks could not be run because the installed Flutter and Dart executables returned `Operation not permitted` (exit 126). No events were sent to an external service during verification.
