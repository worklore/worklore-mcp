# Implementation of Analytics Events

All product analytics events defined in `docs/EVENTS.md` have been implemented across the registration and offers screens using `Analytics.capture`.

## Summary of Changes

### 1. Registration Screen (`lib/screens/registration_screen.dart`)
- **`registration_email_started`**: Tracked via `_onEmailChanged` when the user begins typing into the email text field (fired once when text transitions from empty to non-empty). No PII is passed.
- **`registration_phone_started`**: Tracked via `_onPhoneChanged` when the user begins typing into the phone number text field (fired once when text transitions from empty to non-empty). No PII is passed.
- **`loan_amount_changed`**: Tracked inside `Slider.onChanged` with the chosen amount as an integer: `{'amount': v.round()}`.
- **`terms_accepted`**: Tracked in `CheckboxListTile.onChanged` specifically when the checkbox is checked (`v == true`).
- **`registration_continue_tapped`**: Tracked on Continue button press before navigating to `/offers`, sending `{'amount': _amount.round(), 'terms': _terms}`.

### 2. Offers Screen (`lib/screens/offer_screen.dart`)
- **`offers_scrolled`**: Wrapped the offers list in a `NotificationListener<ScrollNotification>`. When a `ScrollUpdateNotification` occurs with a non-zero scroll delta, `Analytics.capture` is called with `{'offset': notification.metrics.pixels}`.
