# Analytics Implementation Summary

Implemented the analytics events specified in `docs/EVENTS.md` across `lib/screens/registration_screen.dart` and `lib/screens/offer_screen.dart` using `Analytics.capture` from `lib/analytics.dart`.

### Implemented Events

1. **`registration_email_started`** (`lib/screens/registration_screen.dart`):
   - Fired once on the user's first input edit in the email `TextField` using a boolean guard flag (`_emailStartedFired`).
   - Does not send email or any PII in properties.

2. **`registration_phone_started`** (`lib/screens/registration_screen.dart`):
   - Fired once on the user's first input edit in the phone `TextField` using a boolean guard flag (`_phoneStartedFired`).
   - Does not send phone number or any PII in properties.

3. **`loan_amount_changed`** (`lib/screens/registration_screen.dart`):
   - Captured in `Slider.onChangeEnd` when the user finishes moving the slider to avoid event quota exhaustion on every intermediate slider tick.
   - Property: `{'amount': v.round()}` (`amount` as `int`).

4. **`terms_accepted`** (`lib/screens/registration_screen.dart`):
   - Fired when the terms and conditions checkbox transitions to checked (`newValue && !_terms`).
   - No properties sent.

5. **`registration_continue_tapped`** (`lib/screens/registration_screen.dart`):
   - Fired when the user taps the enabled "Continue" button before navigating to `/offers`.
   - Properties: `{'amount': _amount.round(), 'terms': _terms}` (`amount` as `int`, `terms` as `bool`).

6. **`offers_scrolled`** (`lib/screens/offer_screen.dart`):
   - Wrapped `ListView.builder` in a `NotificationListener<ScrollEndNotification>` to capture the event when scrolling ends.
   - Property: `{'offset': notification.metrics.pixels}` (`offset` as `double`).
