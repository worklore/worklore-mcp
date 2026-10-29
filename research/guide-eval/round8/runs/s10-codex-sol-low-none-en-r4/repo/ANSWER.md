# Analytics events implemented

Added all six events from `docs/EVENTS.md` through `Analytics.capture`:

- Registration tracks the first nonempty email and phone edit once per screen visit, without sending either value.
- Each loan slider change sends the selected integer `amount`.
- Checking the terms box sends `terms_accepted`.
- Tapping an enabled Continue button sends `registration_continue_tapped` with integer `amount` and boolean `terms`.
- Offers list scroll updates send `offers_scrolled` with a double `offset`.

Verification: `flutter analyze` completed with no issues.
