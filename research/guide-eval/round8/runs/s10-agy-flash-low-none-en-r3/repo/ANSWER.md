# Analytics Implementation Summary

Implemented the product analytics events specified in `docs/EVENTS.md` across the registration and offers screens using the existing `Analytics` wrapper (`Analytics.capture`).

## Events Implemented

1. `registration_email_started`:
   - Triggered when the user starts typing in the email field (first character entered).
   - Contains no properties (no PII).
   - Implemented in `lib/screens/registration_screen.dart`.

2. `registration_phone_started`:
   - Triggered when the user starts typing in the phone number field (first character entered).
   - Contains no properties (no PII).
   - Implemented in `lib/screens/registration_screen.dart`.

3. `loan_amount_changed`:
   - Triggered when the user adjusts the loan amount slider.
   - Properties: `amount` (`int`, rounded chosen amount).
   - Implemented in `lib/screens/registration_screen.dart`.

4. `terms_accepted`:
   - Triggered when the user ticks the terms and conditions checkbox (`checked == true`).
   - Contains no properties.
   - Implemented in `lib/screens/registration_screen.dart`.

5. `registration_continue_tapped`:
   - Triggered when the user taps the Continue button on the registration screen.
   - Properties: `amount` (`int`), `terms` (`bool`).
   - Implemented in `lib/screens/registration_screen.dart`.

6. `offers_scrolled`:
   - Triggered as the user scrolls the offers list view using a `NotificationListener<ScrollNotification>` listening for `ScrollUpdateNotification`.
   - Properties: `offset` (`double`, `notification.metrics.pixels`).
   - Implemented in `lib/screens/offer_screen.dart`.
