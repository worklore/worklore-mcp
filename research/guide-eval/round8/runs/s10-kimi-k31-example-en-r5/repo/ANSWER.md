# Analytics event implementation

Implemented all events from `docs/EVENTS.md` through the existing `Analytics.capture` wrapper.

- `registration_email_started` and `registration_phone_started`: sent on the first edit of their respective fields, once per registration screen visit. No email address or phone number is included in event properties.
- `loan_amount_changed`: sent when a slider drag ends, with the chosen amount rounded to an integer.
- `terms_accepted`: sent only when the terms checkbox is ticked, not when it is cleared.
- `registration_continue_tapped`: sent when the enabled Continue button is tapped, before navigating to offers, with integer `amount` and boolean `terms` properties.
- `offers_scrolled`: sent when an offers-list scroll ends, with the final scroll offset in logical pixels as a double.

## Colleague's note

Applied the recommendations to guard text-field events so they fire only on the first edit, use `onChangeEnd` for the slider, and use `ScrollEndNotification` instead of scroll updates. This preserves the specified event names and properties while avoiding per-keystroke, per-slider-step, and per-scroll-update event volume. The focus/final-value recommendations did not apply because these events do not require field values; the specification also explicitly prohibits sending email and phone values.

## Verification

`git diff --check` passed. Dart formatting and `flutter analyze` could not be run because the installed Dart/Flutter SDK could not be executed: macOS returned `Operation not permitted` for the SDK binaries.
