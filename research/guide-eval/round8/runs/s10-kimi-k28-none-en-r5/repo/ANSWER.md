# Answer

Implemented all six events from `docs/EVENTS.md` on the registration and
offers screens, calling the existing `Analytics.capture` wrapper
(`lib/analytics.dart`). No PII is sent anywhere, and no screen-view events
were added (those already come from `PosthogObserver`).

## Registration screen (`lib/screens/registration_screen.dart`)

- `registration_email_started` — fires once, the first time the email field
  goes from empty to non-empty (`onChanged`, lines 43–49). Firing per
  keystroke would spam one funnel step, so it fires on "started typing".
- `registration_phone_started` — same pattern for the phone field
  (lines 56–62).
- `loan_amount_changed` — fires from the slider's `onChangeEnd` with
  `{'amount': v.round()}` (int), i.e. once per slider adjustment with the
  chosen amount, instead of on every drag tick (lines 73–74).
- `terms_accepted` — fires when the checkbox becomes checked (`v == true`);
  unticking sends nothing (lines 80–85).
- `registration_continue_tapped` — fires in the Continue button's
  `onPressed` before navigation, with `amount` (int, `_amount.round()`) and
  `terms` (bool, `_terms`) (lines 90–96).

## Offers screen (`lib/screens/offer_screen.dart`)

- Converted `OfferScreen` from `StatelessWidget` to `StatefulWidget` to hold
  a `ScrollController`.
- `offers_scrolled` — a scroll listener emits
  `{'offset': offset}` (double, current scroll position in pixels) whenever
  the offset has moved at least 50 px since the last emitted event
  (lines 42–49). This guarantees the event fires for any real scroll while
  avoiding per-pixel flooding during a fling. The controller is disposed in
  `dispose()` (lines 51–55).

## Judgment calls (not pinned down by the doc)

- "Started typing" = first empty→non-empty transition, once per field.
- "Moved the slider" = one event per adjustment (`onChangeEnd`) with the
  final chosen amount.
- "Scrolled" = current offset reported on first movement and then on each
  additional 50 px of travel.

## Verification

`flutter analyze` could not run in this environment: the macOS shell refuses
to execute the Flutter SDK (`Operation not permitted` on
`~/development/flutter/bin/flutter`), and the project has no resolved
dependencies yet. As a substitute, I type-checked the actual source files
with the Dart 3.11.5 analyzer against minimal API-faithful stubs of
`package:flutter/material.dart` and `package:posthog_flutter` (in a temp
directory, deleted afterwards). Result: **no issues found**. Worth a real
`flutter analyze` run wherever the Flutter SDK is accessible.

Nothing was deployed, published, or reported to any external service.
