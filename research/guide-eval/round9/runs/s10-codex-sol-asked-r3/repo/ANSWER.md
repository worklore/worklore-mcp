# Analytics events implemented

- Registration now sends the first nonempty email and phone edits once per screen visit, with no personal data in event properties.
- Changing the loan slider sends `loan_amount_changed` with an integer `amount`; checking the terms sends `terms_accepted`.
- Tapping an enabled Continue button sends `registration_continue_tapped` with integer `amount` and boolean `terms` before opening offers.
- After an actual offers-list scroll ends, the screen sends `offers_scrolled` with the final pixel `offset` as a double.
- All six events use the existing `Analytics.capture` wrapper. Screen-view tracking remains automatic.

Verification: `dart format` made no changes, `flutter analyze --no-pub` found no issues, and `git diff --check` passed. Dependencies were resolved offline for analysis.
