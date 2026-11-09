# Analytics implementation

Implemented all events from `docs/EVENTS.md` through the existing `Analytics.capture` wrapper.

- Registration email and phone start events fire once per screen instance after the first non-empty input, without sending either field's value.
- Loan amount slider changes send `loan_amount_changed` with the chosen amount as an integer.
- Checking the terms checkbox sends `terms_accepted`; unchecking it does not.
- Tapping Continue sends `registration_continue_tapped` with the integer loan amount and boolean terms state before opening the offers screen.
- Scrolling the offers list sends `offers_scrolled` with the current scroll offset as a double.

## Validation

- `git diff --check` passed.
- `dart format` and `flutter analyze` could not run because the installed Dart and Flutter executables were rejected by the OS with `Operation not permitted` (exit code 126).
