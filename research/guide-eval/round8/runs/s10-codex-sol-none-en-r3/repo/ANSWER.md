# Analytics events implemented

- Registration sends `registration_email_started` and `registration_phone_started` once per screen visit when the user first enters text. Neither event includes personal data.
- Slider changes send `loan_amount_changed` with the selected integer `amount`. Checking the terms sends `terms_accepted`; unchecking does not. A valid Continue tap sends `registration_continue_tapped` with integer `amount` and boolean `terms` before opening offers.
- Offers sends `offers_scrolled` with the final double pixel `offset` after a scroll ends, once per scroll action.
- All events use the existing `Analytics.capture` wrapper. Automatic screen view tracking remains in place.

Verification: `dart format` and `git diff --check` passed. `flutter analyze --no-pub` could not complete because this checkout has no resolved Flutter/PostHog dependencies. No dependencies were fetched and no app was run, so no analytics data was sent.
