# What was done

Implemented all six events from `docs/EVENTS.md` on the registration and offers
screens, going through the existing `Analytics` wrapper in `lib/analytics.dart`
(no changes to the wrapper itself, no new dependencies, nothing sent anywhere
by me — events are only captured at runtime by the app).

## Registration screen (`lib/screens/registration_screen.dart`)

- `registration_email_started` — fires once, on the first non-empty keystroke
  in the email field (tracked with a `_emailStarted` flag so re-typing or
  deleting doesn't re-fire). No properties; the email value is never sent (PII).
- `registration_phone_started` — same pattern for the phone field
  (`_phoneStarted` flag). No properties; the phone number is never sent (PII).
- `loan_amount_changed` — fired from the slider's `onChanged`, with
  `{'amount': v.round()}` (int, per spec).
- `terms_accepted` — fired only when the checkbox is ticked (not when unticked),
  no properties.
- `registration_continue_tapped` — fired in the Continue button handler before
  navigating, with `{'amount': _amount.round(), 'terms': _terms}` (int and bool,
  per spec).

## Offers screen (`lib/screens/offer_screen.dart`)

- `offers_scrolled` — the `ListView` is wrapped in a
  `NotificationListener<ScrollUpdateNotification>`; each scroll update captures
  `{'offset': notification.metrics.pixels}` (double, per spec). The widget
  remains `StatelessWidget`; no `ScrollController`/dispose needed.

## Decisions and notes

- "Started typing" is interpreted as the first transition from empty to
  non-empty in each field, fired at most once per screen visit.
- `terms_accepted` fires on tick only, matching "user ticked the checkbox".
- `offers_scrolled` fires on every scroll-update notification while the list
  moves, since the spec defines no throttle. If the funnel needs one event per
  scroll gesture, the listener is the single place to change.
- Event names and property names/types match `docs/EVENTS.md` exactly; no
  email/phone values are sent as properties.

## Verification

The changes were reviewed against the spec, but `flutter analyze` / `dart` could
not be run in this environment (the installed SDK at
`/Users/valentinakoniukhova/development/flutter/bin` fails with "Operation not
permitted"). Recommend running `flutter analyze` where the toolchain is allowed.
