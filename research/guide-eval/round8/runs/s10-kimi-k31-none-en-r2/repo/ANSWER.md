# Analytics events

Implemented all events from `docs/EVENTS.md` using the existing `Analytics.capture` wrapper.

- `lib/screens/registration_screen.dart`
  - Sends `registration_email_started` and `registration_phone_started` once, on the first change to each field, without sending field values.
  - Sends `loan_amount_changed` when the slider changes, with the chosen integer `amount`.
  - Sends `terms_accepted` only when the checkbox becomes checked.
  - Sends `registration_continue_tapped` before navigation, with integer `amount` and boolean `terms` properties.
- `lib/screens/offer_screen.dart`
  - Sends `offers_scrolled` for offer-list scroll updates, with the current double `offset` in pixels.

No screen-view events or external reporting were added.

## Verification

`git diff --check` passed. Dart formatting and Flutter analysis could not be run because the installed Flutter and Dart launchers fail with `Operation not permitted` in this environment.
