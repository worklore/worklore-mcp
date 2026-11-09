# Analytics events implementation

Implemented all six events from `docs/EVENTS.md` on the registration and
offers screens, going through the existing `Analytics.capture` wrapper in
`lib/analytics.dart` (no PII is sent as properties, per the spec notes).

## Changes

`lib/screens/registration_screen.dart`
- `registration_email_started` — fired once, the first time the email field
  becomes non-empty (flag `_emailStarted` so it doesn't re-fire on every
  keystroke).
- `registration_phone_started` — same pattern for the phone field.
- `loan_amount_changed` — fired from the slider's `onChangeEnd` with
  `{'amount': v.round()}` (int). `onChangeEnd` is used instead of
  `onChanged` because `onChanged` fires on every pixel of a drag, which
  would send dozens of events per gesture; the end-of-drag value is the
  chosen amount the spec asks for.
- `terms_accepted` — fired only when the checkbox is ticked (not when
  unticked).
- `registration_continue_tapped` — fired in the Continue button's
  `onPressed` with `{'amount': _amount.round(), 'terms': _terms}`
  (int, bool), just before navigating to `/offers`.

`lib/screens/offer_screen.dart`
- Converted `OfferScreen` from `StatelessWidget` to `StatefulWidget` to
  own a `ScrollController`.
- `offers_scrolled` — fired once per visit to the screen, the first time
  the list scrolls past offset 0, with `{'offset': offset}` (double).
  The controller is disposed in `dispose()`.

## Verification

- `dart format --output=none lib/` parses all files with no errors.
- Could not run `flutter analyze` / `flutter test`: the Flutter SDK at
  `~/development/flutter` is permission-blocked from this shell
  ("Operation not permitted" from macOS), and the standalone Homebrew
  Dart can't resolve Flutter SDK packages. The changes are type-checked
  by manual review only; they use the same APIs and patterns already
  present in the codebase. Worth running `flutter analyze` on a machine
  where the Flutter toolchain is accessible.

## Decisions made (not specified in the doc)

- "Started typing" events fire once per screen visit (first non-empty
  character), not per keystroke.
- `offers_scrolled` fires once per visit at the first scroll past the
  top, rather than on every scroll update (which would spam one event
  per frame while scrolling).
- No screen-view events were added — the doc says those are automatic
  via `PosthogObserver` in `lib/main.dart`.
