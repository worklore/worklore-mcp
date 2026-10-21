# Analytics Implementation Summary

Implemented the 6 product funnel analytics events defined in `docs/EVENTS.md` across `RegistrationScreen` and `OfferScreen` using `Analytics.capture`.

## Implemented Events

### Registration Screen (`lib/screens/registration_screen.dart`)
1. **`registration_email_started`**
   - Triggered when the user starts typing their email (the first time text is entered in the email `TextField`).
   - Managed via a boolean flag (`_emailStarted`) to ensure it only fires once when typing begins.
   - No properties sent (preserving PII privacy).

2. **`registration_phone_started`**
   - Triggered when the user starts typing their phone number (the first time text is entered in the phone `TextField`).
   - Managed via a boolean flag (`_phoneStarted`) to ensure it only fires once when typing begins.
   - No properties sent (preserving PII privacy).

3. **`loan_amount_changed`**
   - Triggered in the `Slider` widget's `onChangeEnd` callback when the user finishes moving the slider thumb.
   - Property sent: `amount` (as an `int`, via `v.round()`).

4. **`terms_accepted`**
   - Triggered in `CheckboxListTile.onChanged` when the checkbox value is ticked (`v == true`).
   - No properties sent.

5. **`registration_continue_tapped`**
   - Triggered inside the `FilledButton.onPressed` handler when the enabled Continue button is pressed, right before navigating to `/offers`.
   - Properties sent: `amount` (`int`, `_amount.round()`) and `terms` (`bool`, `_terms`).

### Offers Screen (`lib/screens/offer_screen.dart`)
6. **`offers_scrolled`**
   - Wrapped `ListView.builder` with a `NotificationListener<ScrollEndNotification>`.
   - Fires when the user finishes a scroll gesture on the offers list.
   - Property sent: `offset` (`double`, from `notification.metrics.pixels`).
