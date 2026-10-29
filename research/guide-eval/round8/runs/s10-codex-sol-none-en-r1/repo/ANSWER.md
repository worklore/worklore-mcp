# Analytics events implemented

- Registration sends `registration_email_started` and `registration_phone_started` once when typing first begins in each field. Neither event includes the entered value.
- Slider changes send `loan_amount_changed` with the selected integer `amount`. Checking the terms sends `terms_accepted`. A valid Continue tap sends `registration_continue_tapped` with integer `amount` and boolean `terms` before opening offers.
- Offers sends `offers_scrolled` after a scroll that moved the list, with the final scroll `offset` as a double.

All six events use the existing `Analytics.capture` wrapper. Screen view tracking is unchanged.

Verification: `flutter analyze --no-pub` completed with no issues after resolving dependencies offline.
