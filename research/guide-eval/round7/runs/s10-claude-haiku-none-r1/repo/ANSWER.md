# Analytics events: registration and offers screens

Implemented all six events from `docs/EVENTS.md`, sent through the existing
`Analytics.capture` wrapper. Edited two files:

- `lib/screens/registration_screen.dart`
- `lib/screens/offer_screen.dart`

`flutter analyze` reports no issues. The code is formatted with `dart format`.
Nothing was run on a device, and no events were sent to PostHog.

## What each event does

| Event | Where | Behaviour |
|---|---|---|
| `registration_email_started` | Email field `onChanged` | Fires on the first change in the field, once per screen visit. |
| `registration_phone_started` | Phone field `onChanged` | Same, for the phone field. |
| `loan_amount_changed` | Slider `onChangeEnd` | Fires once when the drag ends, with `amount: v.round()`. |
| `terms_accepted` | Checkbox `onChanged` | Fires only when the box becomes ticked, not when it is unticked. |
| `registration_continue_tapped` | Continue button `onPressed` | Fires with `amount: _amount.round()` and `terms: _terms`, then navigates. |
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` around the offers `ListView` | Fires once per finished scroll with `offset: metrics.pixels`. |

## Judgment calls

- **Slider uses `onChangeEnd`, not `onChanged`.** `onChanged` fires on every
  drag tick, which would flood the free tier. The spec says "the chosen
  amount", so the value at the end of the drag is the one that matters.
  If product wants every movement, switch the callback to `onChanged`.
- **Offers scroll uses `ScrollEndNotification`, not a `ScrollController`.**
  This sends one event per gesture instead of one per frame. It also
  needed no state change, so `OfferScreen` stays stateless.
- **"Started" events fire once per screen visit**, tracked by a bool on the
  state. They reset when the user leaves and comes back, because the state is
  recreated.
- **No PII.** Email and phone values are never sent. Only the amount and the
  terms flag are included as properties.

## Not changed

- `docs/EVENTS.md` still says "Status: approved, waiting for implementation".
  I left it alone, since that status is product's to update.
- The PostHog key in `lib/analytics.dart` is still `phc_REPLACE_ME_IN_CI`.
  Real events will only go out once CI injects the key. I did not touch it.
- Nothing is committed.

## Environment note

Running `flutter analyze` and `flutter pub get` rewrote
`analysis_options.yaml` and created `.dart_tool/` and `pubspec.lock`. I
reverted the config and deleted the generated files, so the diff contains
only the two screen files.
