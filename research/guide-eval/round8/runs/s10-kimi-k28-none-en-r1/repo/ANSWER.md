# Analytics events implementation

Implemented all six events from `docs/EVENTS.md` using the existing
`Analytics.capture()` wrapper in `lib/analytics.dart`. No new dependencies,
no changes to the wrapper itself.

## Registration screen — `lib/screens/registration_screen.dart`

- `registration_email_started` — fired once, the first time the email field
  goes from empty to non-empty (`_onEmailChanged`). The email text itself is
  never sent (PII, per the doc's notes).
- `registration_phone_started` — same pattern for the phone field
  (`_onPhoneChanged`). Phone number never sent.
- `loan_amount_changed` — fired on the slider's `onChangeEnd`, i.e. once per
  drag gesture with the final chosen value, as `{'amount': int}`. Firing on
  `onChanged` instead would emit dozens of intermediate values per gesture,
  which doesn't match "the chosen amount".
- `terms_accepted` — fired only when the checkbox is ticked (`v == true`),
  not when unticked.
- `registration_continue_tapped` — fired in the Continue button's
  `onPressed`, before navigation, with `{'amount': int, 'terms': bool}` from
  the current widget state.

The "started" events use one-shot flags (`_emailStartedSent`,
`_phoneStartedSent`) so they fire once per visit even if the user clears and
retypes the field.

## Offers screen — `lib/screens/offer_screen.dart`

- Converted `OfferScreen` from `StatelessWidget` to `StatefulWidget` to hold
  a `ScrollController`.
- `offers_scrolled` — fired once per visit, the first time the list scrolls
  to a non-zero offset, with `{'offset': double}`. A plain scroll listener
  fires on every frame, so a one-shot flag guards it. Re-entering the screen
  creates a fresh state, so the event can fire once per visit.

## Verification

Could not run `flutter analyze` / `dart analyze`: both binaries exist on the
machine but the sandbox refuses to execute them ("Operation not permitted").
The changes were reviewed manually instead — imports, types (`int` amounts,
`bool` terms, `double` offset all match `Map<String, Object>`), and the
one-shot flag logic. Worth running `flutter analyze` locally to confirm.

## Assumptions

- "Started typing" = first transition from empty to non-empty, once per visit.
- "The chosen amount" = the slider value at the end of a drag gesture.
- `terms_accepted` only fires on tick, not untick.
- `offers_scrolled` fires once per screen visit with the offset at first
  scroll, rather than per scroll frame.

All debatable points follow the funnel use case in `docs/EVENTS.md`: one
event per funnel step per user, not continuous telemetry.
