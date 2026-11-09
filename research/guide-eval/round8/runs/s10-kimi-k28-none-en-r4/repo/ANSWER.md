# What was done

Implemented all six events from `docs/EVENTS.md` on the two screens, sent
through the existing `Analytics.capture` wrapper (`lib/analytics.dart`).
No email/phone values are sent as properties, per the PII note.

## Registration screen (`lib/screens/registration_screen.dart`)

- `registration_email_started` — fires once, the first time the email field
  becomes non-empty (`_emailStartedSent` flag). Keystrokes after that do not
  re-fire it, so one funnel step per user.
- `registration_phone_started` — same pattern for the phone field.
- `loan_amount_changed` — fires from the slider's `onChangeEnd` with
  `{'amount': v.round()}`. The spec says the property is "the chosen amount",
  so the event carries the value the user settled on, once per drag, instead
  of one event per pixel of a `onChanged` stream.
- `terms_accepted` — fires when the checkbox is ticked (`v == true`);
  unticking sends nothing.
- `registration_continue_tapped` — fires in the Continue button's `onPressed`
  (which is only non-null when the form is valid) with
  `{'amount': _amount.round(), 'terms': _terms}`, right before navigating to
  `/offers`.

## Offers screen (`lib/screens/offer_screen.dart`)

Converted `OfferScreen` from `StatelessWidget` to `StatefulWidget` to hold a
`ScrollController` (created in `initState`, disposed in `dispose`).

- `offers_scrolled` — a listener on the controller sends
  `{'offset': _scrollController.offset}` (scroll position in pixels, a
  double) after every 100 px of accumulated scrolling. The 100 px threshold
  keeps a continuous drag from flooding one event per pixel; on the PostHog
  free tier that volume would burn through the monthly event quota quickly.

## Other changes

- `README.md`: updated the analytics paragraph, which still claimed the
  screens send no product events.

## Verification

- `dart format` is clean and stable on `lib/`.
- `dart analyze` could not be run to completion in this environment: the
  Flutter SDK under `~/development/flutter` is not executable/readable from
  this shell (macOS "Operation not permitted"), so `package:flutter` and
  `package:posthog_flutter` cannot be resolved and no `pub get` is possible.
  The analyzer errors that do appear are exclusively those unresolved package
  URIs (including in untouched `lib/main.dart` and `lib/analytics.dart`),
  i.e. pre-existing environmental failures, none pointing at the new code.
  Worth running `flutter analyze` once on a machine with the Flutter SDK
  available.
