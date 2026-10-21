# Analytics events implemented

- Registration sends `registration_email_started` and `registration_phone_started` once when each field first receives input. Neither event includes contact details.
- The loan slider sends `loan_amount_changed` when an interaction ends with a changed value, including the chosen integer `amount`.
- Accepting the checkbox sends `terms_accepted`. Tapping an enabled Continue button sends `registration_continue_tapped` with integer `amount` and boolean `terms` before opening offers.
- Offers sends `offers_scrolled` once after the first user scroll ends, with the list's double `offset`.

All events use the existing `Analytics.capture` wrapper. `flutter analyze` completed with no issues.
