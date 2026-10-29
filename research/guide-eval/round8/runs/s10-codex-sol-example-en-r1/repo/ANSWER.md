# Analytics events implemented

Added all six events from `docs/EVENTS.md` to the registration and offers screens through the existing `Analytics.capture` wrapper. Email and phone events fire on the first nonempty edit for each registration flow, with no typed values sent. The loan amount event fires when a slider interaction ends and sends the chosen integer amount. Accepting the terms fires only when the checkbox becomes checked. Continue sends the amount and terms state before navigating. The offers event fires when vertical scrolling ends and sends the list offset as a double.

The colleague's note applied to the text fields, slider, and offers list because their change callbacks can fire repeatedly during one interaction. I used once-only flags for text input, `onChangeEnd` for the slider, and `ScrollEndNotification` for the list. The focus and final-value advice did not apply because these events need neither focus tracking nor email or phone values. The flags last for the registration flow, including a return from the offers screen to the still-mounted registration screen. The suggested PostHog debug dashboard check was not run because it would require sending events to an external service.

Verification: `flutter analyze` completed with no issues.
