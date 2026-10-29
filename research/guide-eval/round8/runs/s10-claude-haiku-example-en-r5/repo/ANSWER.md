# Analytics events: registration and offers screens

Implemented the six events in `docs/EVENTS.md` on the two screens, using the
existing `Analytics.capture` wrapper in `lib/analytics.dart`. Event names and
properties match the spec exactly. No email or phone values are sent.

## What changed

`lib/screens/registration_screen.dart`

| Event | Trigger | Properties |
|---|---|---|
| `registration_email_started` | First `onChanged` of the email field on this screen state | — |
| `registration_phone_started` | First `onChanged` of the phone field on this screen state | — |
| `loan_amount_changed` | Slider `onChangeEnd` (once per drag, on release) | `amount` = `v.round()` |
| `terms_accepted` | Checkbox `onChanged` with `v == true` | — |
| `registration_continue_tapped` | Continue `onPressed`, before navigating | `amount` = `_amount.round()`, `terms` = `_terms` |

- Email and phone each have a `bool` flag (`_emailStarted`, `_phoneStarted`) so
  the "started" event fires once per visit instead of once per keystroke.
- The slider keeps `onChanged` for the UI update only. The event moved to
  `onChangeEnd`.

`lib/screens/offer_screen.dart`

| Event | Trigger | Properties |
|---|---|---|
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` around the list | `offset` = `metrics.pixels` |

- Uses `ScrollEndNotification`, so it fires once per scroll gesture rather than
  on every scroll update. The listener returns `false` so the list still gets
  the notification.

## Colleague note: what applied

The note was a write-up from another team about a similar Flutter/PostHog
problem. Applied parts:

- **Once-per-visit flag for text fields.** Applied to the two `*_started`
  events. The spec says "started typing", so once per visit is the right reading.
- **Slider: `onChanged` → `onChangeEnd`.** Applied to `loan_amount_changed`.
  The spec says "moved the slider", so one event per drag is the intent.
- **Scrolls: `ScrollEndNotification`, not `ScrollUpdateNotification`.** Applied
  to `offers_scrolled`.

Parts that did not apply:

- **Focus-node events and "final value on focus lost".** The spec has no
  focus-based or "final value" event. Nothing in the spec needs these.
- **Grep check for existing per-change captures.** Nothing was sending events
  before this change, so there were no existing offenders to fix.
- **"Which events may stay per-change."** The spec doesn't ask for any
  per-change events, so none were kept.
- **Dashboard verification.** Not run (see below).

## Decisions to review

- **`loan_amount_changed` also fires on a tap** without a drag, since
  `onChangeEnd` runs for taps too. That still counts as the user moving the slider.
- **`terms_accepted` fires only when ticked.** Unticking does not send an event.
- **`registration_continue_tapped` fires only when the button is enabled.**
  A disabled `FilledButton` ignores taps. Enabling also requires `_terms == true`,
  so `terms` will always be `true` in this event. If product wants disabled taps
  counted too, that needs a different widget and should be decided first.
- **`offers_scrolled` `offset` is the absolute position** (`metrics.pixels`) at
  the end of the scroll, not the distance of that one gesture. The spec says
  "how far they scrolled", so this is my reading. Say if you want the delta.
- **Per-visit flags reset on a new screen state.** Popping back from offers keeps
  the existing registration state, so the flags survive. A fresh visit creates
  a new state and fires the `*_started` events again.

## Verification

- `dart format` applied to `lib/`.
- `flutter analyze`: no issues found.
- **Not verified on a device.** I did not run the app or check events in
  PostHog. The key in `lib/analytics.dart` is still `phc_REPLACE_ME_IN_CI`.
- `flutter pub get` changed `analysis_options.yaml`, added `.dart_tool/` and
  created `pubspec.lock`. I reverted the config file and removed the generated
  artifacts, so the diff only touches the two screens and this file.

## Not done

- Nothing committed.
- Nothing sent or published anywhere.
