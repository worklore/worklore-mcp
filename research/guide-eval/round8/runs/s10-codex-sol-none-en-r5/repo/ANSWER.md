# Analytics events implemented

- Registration now sends `registration_email_started` and `registration_phone_started` once when typing begins, without sending either field's value.
- Moving the loan slider sends `loan_amount_changed` with the selected integer `amount`. Checking the terms box sends `terms_accepted`.
- Tapping an enabled Continue button sends `registration_continue_tapped` with integer `amount` and boolean `terms` before opening the offers screen.
- The offers screen sends `offers_scrolled` after each completed scroll that moved the list, with the final `offset` as a double. This avoids an event for every scroll frame.

All events use the existing `Analytics.capture` wrapper. Screen view tracking remains handled by the existing observer.

Verification: `flutter analyze --no-pub` completed with no issues after resolving dependencies from the local cache.
