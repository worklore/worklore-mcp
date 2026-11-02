# Analytics events implemented

- Added all six events from `docs/EVENTS.md` to the registration and offers screens through `Analytics.capture`.
- Email and phone start events fire once per screen visit when the user first enters text. Neither value is included in event properties.
- The loan amount event fires when a slider gesture ends with the selected integer amount. Accepting the terms fires its event when the checkbox becomes checked. Continue sends the current integer amount and boolean terms value before opening offers.
- The offers event fires after a user scroll finishes with the list's double offset, avoiding an event for every scroll update.

Verification: `flutter analyze` completed with no issues. Runtime delivery to PostHog was not tested.
