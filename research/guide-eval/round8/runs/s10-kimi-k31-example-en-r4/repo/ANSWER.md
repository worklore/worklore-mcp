# Analytics event implementation

Implemented all events from `docs/EVENTS.md` through the existing `Analytics.capture` wrapper.

## Registration screen

In `lib/screens/registration_screen.dart`:

- `registration_email_started` fires on the first email edit per screen state, guarded by `_emailInputFired`.
- `registration_phone_started` fires on the first phone edit per screen state, guarded by `_phoneInputFired`.
- `loan_amount_changed` fires from the slider's `onChangeEnd`, with the final `amount` as a rounded integer.
- `terms_accepted` fires only when the checkbox changes to checked, not when it is unchecked.
- `registration_continue_tapped` fires when the enabled Continue button is tapped, before navigation, with integer `amount` and boolean `terms` properties.
- Email addresses and phone numbers are never included in event properties.

## Offers screen

In `lib/screens/offer_screen.dart`:

- Wrapped the offers list in `NotificationListener<ScrollEndNotification>`.
- `offers_scrolled` fires when a scroll ends, with `offset` set to `notification.metrics.pixels` (a double), rather than firing on every scroll update.

## Colleague's note

The applicable guidance was:

- Guard text-field `onChanged` analytics with once-only flags to avoid an event per keystroke.
- Put slider analytics in `onChangeEnd` while leaving UI updates in `onChanged`.
- Use `ScrollEndNotification` instead of scroll-update notifications or controller listeners.
- Keep the specified event names and properties unchanged and avoid sensitive field values.

The focus-loss/final-field-value guidance did not apply because none of these events requires a text field's final value. No external PostHog reporting, deployment, or live quota reproduction was performed.

## Verification

- `git diff --check` passed.
- `dart format` and `flutter analyze` could not run: macOS returned `Operation not permitted` (exit code 126) for both SDK executables under `/Users/valentinakoniukhova/development/flutter/bin/`.
