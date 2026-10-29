# Analytics events implemented

- Registration tracks the first nonempty email and phone edits once per screen visit, without sending either value.
- Loan slider changes send `loan_amount_changed` with the selected integer amount. Checking the terms sends `terms_accepted`; tapping Continue sends `registration_continue_tapped` with the amount and terms state.
- The offers list sends `offers_scrolled` after each scroll with the final offset as a double.
- All events use `Analytics.capture`. Existing automatic screen view tracking remains in place.

Verification: `flutter analyze` completed with no issues.
