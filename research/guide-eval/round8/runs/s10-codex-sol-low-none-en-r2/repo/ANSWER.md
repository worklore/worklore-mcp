# Analytics events

Implemented all six events from `docs/EVENTS.md` through `Analytics.capture`.

- Registration sends one event when the user first types in each contact field, an integer amount for each slider change, an event when terms are checked, and the amount and terms state when Continue is tapped.
- Offers sends the current scroll offset as a double for user drag updates.
- Email and phone values are never sent as event properties.

Validation: `flutter analyze` completed with no issues.
