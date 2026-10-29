# Implementation Summary

Implemented the analytics events defined in **docs/EVENTS.md** on the registration and offers screens using the existing `Analytics` wrapper.

## What was added

1. **Analytics import** on both screens.
   ```dart
   import '../analytics.dart';
   ```
2. **State flags** in `RegistrationScreen` to ensure events fire only once per screen visit:
   ```dart
   bool _emailStarted = false;
   bool _phoneStarted = false;
   bool _termsAcceptedFired = false;
   ```
3. **Email & phone start events** – captured on the first `onChanged` callback.
   ```dart
   if (!_emailStarted) { Analytics.capture('registration_email_started'); _emailStarted = true; }
   if (!_phoneStarted) { Analytics.capture('registration_phone_started'); _phoneStarted = true; }
   ```
4. **Loan amount change** – moved from `onChanged` to `onChangeEnd` to fire once per drag, sending the chosen amount as a property.
   ```dart
   onChangeEnd: (v) { Analytics.capture('loan_amount_changed', {'amount': v.round()}); }
   ```
5. **Terms accepted** – captured the first time the checkbox is checked.
   ```dart
   if (newVal && !_termsAcceptedFired) { Analytics.capture('terms_accepted'); _termsAcceptedFired = true; }
   ```
6. **Offers list scroll** – wrapped the scaffold in a `NotificationListener<ScrollEndNotification>` and sent the scroll offset.
   ```dart
   Analytics.capture('offers_scrolled', {'offset': notification.metrics.pixels});
   ```

## Parts of the colleague’s note that were useful

- **Use a flag for TextField `onChanged`** to send the event only once per screen visit.
- **Move slider analytics to `onChangeEnd`** so it fires once per drag.
- **Listen for `ScrollEndNotification`** instead of per‑pixel scroll updates.
- **Keep event names and properties unchanged** while adjusting when they fire.

These patterns directly guided the changes above, ensuring we stay within the event quota while preserving the required analytics data.

---

All code changes are limited to the existing project directory and no external services are invoked.