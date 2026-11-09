# Analytics implementation

Implemented all events from `docs/EVENTS.md` using the existing `Analytics.capture` wrapper.

## Registration screen

- `registration_email_started`: sent on the first non-empty email edit.
- `registration_phone_started`: sent on the first non-empty phone edit.
- `loan_amount_changed`: sent when the slider changes, with the chosen amount rounded to an integer in `amount`.
- `terms_accepted`: sent when the terms checkbox is ticked, not when it is cleared.
- `registration_continue_tapped`: sent before opening the offers screen, with integer `amount` and boolean `terms` properties.

The email address and phone number are never included in event properties.

## Offers screen

- `offers_scrolled`: sent for offer-list scroll updates, with the current scroll position as a double in `offset`.

## Verification

- `git diff --check` passed.
- `dart format lib/screens/registration_screen.dart lib/screens/offer_screen.dart` and `flutter analyze` could not run because the local Dart and Flutter executables returned `Operation not permitted` (exit code 126).
