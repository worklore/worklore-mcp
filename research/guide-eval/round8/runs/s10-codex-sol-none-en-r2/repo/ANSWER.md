# Analytics events implemented

- Registration now captures the first email and phone edits, completed loan amount changes, each acceptance of the terms, and valid Continue taps.
- Offers now captures the final scroll offset when a list scroll ends.
- Events use the existing `Analytics.capture` wrapper and the names and property types in `docs/EVENTS.md`. Email and phone values are never sent.

Verification: `flutter analyze --no-pub` passed after resolving dependencies offline.
