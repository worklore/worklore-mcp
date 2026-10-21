# Analytics events

Implemented all six events in `docs/EVENTS.md` using the existing `Analytics.capture` wrapper.

- Registration records email and phone typing once per screen visit, without sending either value.
- The loan slider records the selected integer amount at the end of each change.
- Accepting the terms records `terms_accepted`; tapping Continue records the current amount and terms value before navigating.
- The offers list records its double scroll offset when a scroll ends, including a return to the top.

Verification: `flutter analyze --no-pub` passed with no issues after offline dependency resolution. No external service was contacted.
