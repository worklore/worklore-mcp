# Implementation of Analytics Events

All product events specified in `docs/EVENTS.md` have been implemented on the registration and offers screens using `Analytics.capture(...)`:

1. **`registration_email_started`** (`lib/screens/registration_screen.dart`):
   - Fired the first time the user types in the email text field (`_emailStarted` flag ensures it triggers once per entry).
   - No PII is included in the event payload.

2. **`registration_phone_started`** (`lib/screens/registration_screen.dart`):
   - Fired the first time the user types in the phone number text field (`_phoneStarted` flag ensures it triggers once per entry).
   - No PII is included in the event payload.

3. **`loan_amount_changed`** (`lib/screens/registration_screen.dart`):
   - Fired in the `Slider`'s `onChanged` callback with properties `{'amount': v.round()}` (integer value).

4. **`terms_accepted`** (`lib/screens/registration_screen.dart`):
   - Fired in `CheckboxListTile` when the user transitions from unchecked to checked.

5. **`registration_continue_tapped`** (`lib/screens/registration_screen.dart`):
   - Fired when the user taps the Continue button prior to navigation to `/offers`, with properties `{'amount': _amount.round(), 'terms': _terms}` (`amount` as int, `terms` as bool).

6. **`offers_scrolled`** (`lib/screens/offer_screen.dart`):
   - Converted `OfferScreen` to a `StatefulWidget` using a `ScrollController`.
   - Captures `offers_scrolled` with property `{'offset': _scrollController.offset}` (double) whenever the list view is scrolled.
