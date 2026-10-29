# Analytics Events Implementation

Implemented the product funnel analytics events specified in `docs/EVENTS.md` using the `Analytics.capture` wrapper across the registration and offers screens:

### 1. `registration_screen.dart`

- **`registration_email_started`**: Added `_emailStarted` flag to trigger `Analytics.capture('registration_email_started')` once when the user begins typing into the email `TextField` (`text.isNotEmpty`). No PII is sent.
- **`registration_phone_started`**: Added `_phoneStarted` flag to trigger `Analytics.capture('registration_phone_started')` once when the user begins typing into the phone `TextField` (`text.isNotEmpty`). No PII is sent.
- **`loan_amount_changed`**: Added `onChangeStart`, `onChanged`, and `onChangeEnd` handlers to capture `loan_amount_changed` with `{'amount': amount}` as an `int` representing the chosen amount, avoiding duplicate event flooding during continuous drag interactions while supporting both gesture-based adjustments and direct value changes.
- **`terms_accepted`**: Added tracking in the `CheckboxListTile.onChanged` handler to trigger `Analytics.capture('terms_accepted')` when the user ticks the terms and conditions checkbox (`checked && !_terms`).
- **`registration_continue_tapped`**: Added tracking in the Continue `FilledButton.onPressed` handler to trigger `Analytics.capture('registration_continue_tapped', {'amount': _amount.round(), 'terms': _terms})` before navigating to `/offers`.

### 2. `offer_screen.dart`

- **`offers_scrolled`**: Wrapped the offers `ListView.builder` with `NotificationListener<ScrollEndNotification>` to trigger `Analytics.capture('offers_scrolled', {'offset': notification.metrics.pixels})` with the scroll offset as a `double` when the user scrolls the list.
