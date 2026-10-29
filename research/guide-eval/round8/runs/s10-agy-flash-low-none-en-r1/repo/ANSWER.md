# Analytics Events Implementation

The analytics events specified in `docs/EVENTS.md` have been implemented across the registration and offers screens using the existing `Analytics` wrapper (`Analytics.capture`).

## Summary of Changes

### 1. Registration Screen (`lib/screens/registration_screen.dart`)
- **`registration_email_started`**: Tracked via `_onEmailChanged` on the email `TextField` when the user types the first character (`_emailStarted` flag prevents duplicate events and ensures no PII is sent).
- **`registration_phone_started`**: Tracked via `_onPhoneChanged` on the phone `TextField` when the user types the first character (`_phoneStarted` flag prevents duplicate events and ensures no PII is sent).
- **`loan_amount_changed`**: Tracked in `_onAmountChanged` when the loan amount slider is moved, sending `{'amount': value.round()}` (integer).
- **`terms_accepted`**: Tracked in `_onTermsChanged` when the checkbox transitions to checked/true.
- **`registration_continue_tapped`**: Tracked in `_onContinuePressed` when the Continue button is tapped, sending `{'amount': _amount.round(), 'terms': _terms}` (`amount` as `int`, `terms` as `bool`).

### 2. Offers Screen (`lib/screens/offer_screen.dart`)
- **`offers_scrolled`**: Wrapped the offers `ListView.builder` in a `NotificationListener<ScrollNotification>`. On `ScrollUpdateNotification`, sends `{'offset': notification.metrics.pixels}` (`offset` as `double`).
