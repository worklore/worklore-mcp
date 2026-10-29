# Analytics events

Implemented all six events in `docs/EVENTS.md` through the existing `Analytics.capture` wrapper.

- Registration records the first email and phone input per screen visit, without sending either value.
- The slider records the chosen integer amount when a drag ends. Accepting terms records `terms_accepted`; tapping Continue records the amount and terms state before opening offers.
- Offers records the final double scroll offset when a list scroll ends.

Validation: `flutter analyze` completed with no issues, and `git diff --check` passed.
