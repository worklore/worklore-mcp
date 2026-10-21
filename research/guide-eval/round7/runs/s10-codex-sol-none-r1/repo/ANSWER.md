# Analytics events implemented

- Registration sends `registration_email_started` and `registration_phone_started` once when the user first enters text in each field. Neither event includes the entered value.
- Moving the loan slider sends `loan_amount_changed` with the selected integer `amount`. Checking the terms box sends `terms_accepted` on each transition to accepted.
- Tapping an enabled Continue button sends `registration_continue_tapped` with integer `amount` and boolean `terms` before opening offers.
- The offers list sends `offers_scrolled` with a double `offset` when scrolling ends after the list has moved. One event is sent per completed scroll, avoiding an event for every frame.

All events use the existing `Analytics.capture` wrapper. Screen view tracking remains in the existing navigator observer.

Verification: `flutter analyze --no-pub` reported no issues after resolving dependencies from the local cache. There is no `test` directory, so `flutter test --no-pub` had no tests to run.
