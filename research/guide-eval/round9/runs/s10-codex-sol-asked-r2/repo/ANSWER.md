# Analytics events implemented

- Registration now captures `registration_email_started` and `registration_phone_started` on the first nonempty edit of each field per screen visit. Neither event includes contact details.
- The slider captures `loan_amount_changed` with the selected integer `amount` when its value changes. Checking the terms box captures `terms_accepted`.
- Tapping an enabled Continue button captures `registration_continue_tapped` with integer `amount` and boolean `terms` before opening offers.
- The offers list captures `offers_scrolled` after an actual scroll ends, with its final `offset` as a double.
- All six events use the existing `Analytics.capture` wrapper.

Verification: `dart format --output=none --set-exit-if-changed` passed for both edited screens, and `flutter analyze --no-pub` reported no issues after resolving dependencies with `flutter pub get --offline`.
