# Analytics events

Implemented all six events from `docs/EVENTS.md` through the existing `Analytics.capture` wrapper.

## Registration screen

In `lib/screens/registration_screen.dart`:

- `registration_email_started` fires on the first email edit per screen visit.
- `registration_phone_started` fires on the first phone edit per screen visit.
- `loan_amount_changed` fires when the slider interaction ends, with the final amount rounded to an `int` in `amount`.
- `terms_accepted` fires only when the checkbox changes to checked, not when it is unchecked.
- `registration_continue_tapped` fires when Continue is tapped, with `amount` as an `int` and `terms` as a `bool`.

The email address and phone number are never included in event properties.

## Offers screen

In `lib/screens/offer_screen.dart`, a `NotificationListener<ScrollEndNotification>` sends `offers_scrolled` when a scroll ends. Its `offset` property is the final scroll position in logical pixels, as a `double`.

## Colleague's note

The applicable parts were:

- Guarding text-field events with per-screen-state flags so they fire once on the first edit instead of on every keystroke.
- Using the slider's `onChangeEnd` for analytics while retaining `onChanged` only for UI updates.
- Using `ScrollEndNotification` instead of scroll-update notifications or a scroll-controller listener.

The focus-loss/final-field-value guidance did not apply: the text events represent starting to type and have no properties. The tap/focus-node guidance was also unnecessary because Continue and the checkbox already have suitable action handlers. There were no existing analytics calls to migrate, and no external PostHog reporting or dashboard verification was performed.

## Verification

- `git diff --check` passed.
- `dart format` and `flutter analyze` could not run because macOS returned `Operation not permitted` (exit code 126) for both executables in `/Users/valentinakoniukhova/development/flutter/bin/`.
