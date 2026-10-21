# Analytics Implementation Summary

Implemented the product analytics events specified in [`docs/EVENTS.md`](file:///tmp/h-rVMBgl/docs/EVENTS.md) on the registration and offers screens using the existing [`Analytics`](file:///tmp/h-rVMBgl/lib/analytics.dart) wrapper, adhering to event-quota preservation guidelines.

## Changes Made

### 1. Registration Screen ([`lib/screens/registration_screen.dart`](file:///tmp/h-rVMBgl/lib/screens/registration_screen.dart))
- **`registration_email_started`**: Added `_emailStartedFired` flag. Captured on the first keystroke in the email `TextField.onChanged` callback without sending PII.
- **`registration_phone_started`**: Added `_phoneStartedFired` flag. Captured on the first keystroke in the phone `TextField.onChanged` callback without sending PII.
- **`loan_amount_changed`**: Moved capture from `onChanged` to `Slider.onChangeEnd` to fire once per drag gesture when released instead of on every tick, sending `{'amount': v.round()}`.
- **`terms_accepted`**: Captured inside `CheckboxListTile.onChanged` when the checkbox is ticked (`checked == true`).
- **`registration_continue_tapped`**: Captured inside the `FilledButton.onPressed` handler before navigating to `/offers`, sending `{'amount': _amount.round(), 'terms': _terms}`.

### 2. Offers Screen ([`lib/screens/offer_screen.dart`](file:///tmp/h-rVMBgl/lib/screens/offer_screen.dart))
- **`offers_scrolled`**: Wrapped the offers `ListView.builder` inside a `NotificationListener<ScrollEndNotification>` to capture once at scroll completion instead of every scroll update/frame, sending `{'offset': notification.metrics.pixels}`.
