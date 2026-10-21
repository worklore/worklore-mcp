# Analytics events

Added all six events from `docs/EVENTS.md` via `Analytics.capture`. No PII is sent as a property.

**`lib/screens/registration_screen.dart`**
- `registration_email_started` / `registration_phone_started`: fire once, on the first change in each field.
- `loan_amount_changed` (`amount` int): fires from the slider's `onChangeEnd`, so once per drag instead of on every tick. This keeps volume down on the free tier.
- `terms_accepted`: fires only when the box is ticked, not when it is unticked.
- `registration_continue_tapped` (`amount`, `terms`): fires on Continue, before navigating.

**`lib/screens/offer_screen.dart`**
- `offers_scrolled` (`offset` double): `OfferScreen` is now a StatefulWidget. It fires once per visit, when the first vertical scroll ends. The offset is the position at that point.

**Choices to check**
- The spec doesn't say whether the "started" and "scrolled" events should fire once or repeatedly. I chose once, because the funnel only needs the first occurrence.
- `flutter analyze` reports no issues. I did not run the app.
