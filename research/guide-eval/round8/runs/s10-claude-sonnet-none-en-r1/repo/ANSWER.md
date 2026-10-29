# Analytics events

Implemented all six events from `docs/EVENTS.md` via `Analytics.capture`.

**lib/screens/registration_screen.dart**
- `registration_email_started` / `registration_phone_started`: fired once per screen, on the first change in each field. No email/phone values are sent.
- `loan_amount_changed`: fired on slider `onChangeEnd` (not every drag tick) with `amount` as an int.
- `terms_accepted`: fired only when the box is ticked, not when unticked.
- `registration_continue_tapped`: fired on Continue with `amount` (int) and `terms` (bool).

**lib/screens/offer_screen.dart**
- `offers_scrolled`: list wrapped in a `NotificationListener<ScrollEndNotification>`; fires each time a scroll ends, with `offset` (double, pixels).

Judgement calls: "started" events are once-per-screen-instance; slider and scroll events fire at gesture end to avoid flooding. If you want scroll fired only once, it's a one-flag change.
`flutter analyze` reports no issues; the app was not run.
