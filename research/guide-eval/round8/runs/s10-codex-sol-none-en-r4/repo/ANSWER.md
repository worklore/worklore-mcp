# Analytics events

Implemented all six events from `docs/EVENTS.md` on the registration and offers screens through the existing `Analytics.capture` wrapper.

- Email and phone start events fire once per registration screen visit, after the user begins typing. Neither field value is sent.
- The loan amount event sends the selected integer amount when a slider interaction ends. Terms acceptance fires when the checkbox changes from unchecked to checked.
- Continue sends the current integer amount and terms boolean before opening offers.
- Offers scrolling sends the final double offset at the end of each scroll gesture that moved the list.

Verification: `flutter analyze` passed with no issues.
