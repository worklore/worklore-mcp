# kredito

Flutter app (iOS + Android) for a consumer loan broker. The user registers
with an email and a phone number, picks the amount they want to borrow, accepts
the terms and gets a list of offers from partner banks. Two screens so far:
`lib/screens/registration_screen.dart` and `lib/screens/offer_screen.dart`.

Analytics is PostHog (`posthog_flutter`), set up in `lib/analytics.dart` and
`lib/main.dart`; screen views come from `PosthogObserver`. We are on the
PostHog free tier. Product events are defined in `docs/EVENTS.md` and sent
from the registration and offers screens. Send events through
`Analytics.capture` so the key and host stay in one place.
