# Analytics events

Implemented all six events from `docs/EVENTS.md` through `Analytics.capture` on the registration and offers screens.

- Email and phone started events fire on the first edit per registration screen visit. Neither field value is sent.
- Loan amount changes fire when a slider interaction ends, with the chosen amount as an integer.
- Terms acceptance fires when the checkbox becomes checked. Continue taps include the amount and terms state.
- Offers scrolling fires when vertical scrolling ends, with the scroll offset as a double.

The colleague's note applied to the email and phone `onChanged` callbacks, slider movement, and offers scrolling: first-edit flags, `onChangeEnd`, and `ScrollEndNotification` prevent an event for every keystroke, slider step, or scroll update. Its focus-listener advice did not apply because these events do not require a final field value or a focus event. PostHog debug logging and dashboard checks were not used; `flutter analyze` passed with no issues.
