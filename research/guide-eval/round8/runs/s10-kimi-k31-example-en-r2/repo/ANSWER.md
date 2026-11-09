# Analytics implementation

Implemented all six events from `docs/EVENTS.md` through the existing `Analytics.capture` wrapper.

## Registration screen

- `registration_email_started`: fires on the first email edit per screen visit.
- `registration_phone_started`: fires on the first phone edit per screen visit.
- `loan_amount_changed`: fires from the slider's `onChangeEnd` with the chosen integer `amount`; `onChanged` still only updates the UI.
- `terms_accepted`: fires only when the checkbox becomes checked, not when it is unchecked.
- `registration_continue_tapped`: fires when Continue is tapped with integer `amount` and boolean `terms`, before navigating to offers.

No email address or phone number is sent to analytics.

## Offers screen

- `offers_scrolled`: fires from `ScrollEndNotification` with the final scroll `offset` as a double.

## Colleague's note

Applied the once-per-visit flags for text fields, `onChangeEnd` for the slider, and `ScrollEndNotification` for scrolling. These prevent per-keystroke and per-scroll-update event floods. The focus/focus-loss guidance did not apply because these events need only the start of input, not a final field value. No existing event names or properties were changed.

## Verification

Audited the event names, properties, and callbacks against the specification; `git diff --check` passed. `dart format` and `flutter analyze` could not run because the installed Flutter/Dart executables returned `Operation not permitted` in this environment. There are no existing project tests.
