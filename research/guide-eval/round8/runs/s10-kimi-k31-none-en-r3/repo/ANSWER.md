# Analytics implementation

Implemented all six events from `docs/EVENTS.md` through the existing `Analytics.capture` wrapper.

- `lib/screens/registration_screen.dart`
  - Sends `registration_email_started` and `registration_phone_started` once per screen visit, on the first non-empty input.
  - Sends `loan_amount_changed` with the selected integer `amount` whenever the slider changes.
  - Sends `terms_accepted` only when the checkbox is ticked.
  - Sends `registration_continue_tapped` with the current integer `amount` and boolean `terms` before opening the offers screen.
  - Does not include email addresses or phone numbers in event properties.
- `lib/screens/offer_screen.dart`
  - Listens for offer-list scroll updates and sends `offers_scrolled` with the current double `offset` in pixels.

Verification: `git diff --check` passes. Dart formatting and `flutter analyze` could not run because the environment denied execution of both the Dart and Flutter binaries (`Operation not permitted`).
