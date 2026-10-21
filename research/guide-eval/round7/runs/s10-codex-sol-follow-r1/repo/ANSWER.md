# Analytics events implemented

- Registration sends `registration_email_started` and `registration_phone_started` once per screen visit, on the first edit. Neither event includes personal information.
- The loan slider sends `loan_amount_changed` with the selected integer `amount` when a drag ends. The terms checkbox sends `terms_accepted` when it changes to checked.
- Continue sends `registration_continue_tapped` with integer `amount` and boolean `terms` before opening offers.
- The offers list sends `offers_scrolled` with a double `offset` when vertical scrolling ends.

All six events use the existing `Analytics.capture` wrapper. `flutter analyze` passed with no issues. A live PostHog capture check was not run because the configured project key is a placeholder.
