# Analytics events

Implemented all six events from `docs/EVENTS.md` through `Analytics.capture`.

- Registration emits `registration_email_started` and `registration_phone_started` once per screen visit, when the user first enters text. Neither event includes personal information.
- A changed slider selection emits `loan_amount_changed` with the final integer `amount`. Checking the terms emits `terms_accepted`. Tapping an enabled Continue button emits `registration_continue_tapped` with integer `amount` and boolean `terms` before opening offers.
- The offers list emits `offers_scrolled` with the final double pixel `offset` after a scroll ends.

Verification: `dart format`, `flutter analyze --no-pub` (no issues), and `git diff --check` passed. Dependencies were resolved offline for analysis; generated Flutter metadata was removed afterward.
