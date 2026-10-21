# Analytics events implemented

Added all six events from `docs/EVENTS.md` to the registration and offers screens through `Analytics.capture`.

- Email and phone start events fire once per screen instance, when the user first enters text. Neither field's value is sent.
- Amount changes send the chosen amount as an integer. Accepting terms sends `terms_accepted`; tapping Continue sends the integer amount and current terms value.
- Offers scrolling sends `offers_scrolled` after a scroll ends, with the final scroll offset as a double.

Verification: `flutter analyze` completed with no issues.
