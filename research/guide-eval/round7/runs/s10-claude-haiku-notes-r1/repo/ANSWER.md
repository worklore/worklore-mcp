# Registration and offers analytics events

I implemented the six events in `docs/EVENTS.md` on the two screens, using
`Analytics.capture` from `lib/analytics.dart`. Event names and properties match
the spec exactly. Nothing was deployed or sent to PostHog.

## What changed

**`lib/screens/registration_screen.dart`**

| Event | Where it fires |
|---|---|
| `registration_email_started` | Email field `onChanged`, once per screen state (guarded by `_emailStarted`) |
| `registration_phone_started` | Phone field `onChanged`, once per screen state (guarded by `_phoneStarted`) |
| `loan_amount_changed` (`amount`) | Slider `onChangeEnd`, once per drag, with `v.round()` |
| `terms_accepted` | Checkbox `onChanged`, only when the value becomes `true` |
| `registration_continue_tapped` (`amount`, `terms`) | Continue button `onPressed`, before navigating to `/offers` |

**`lib/screens/offer_screen.dart`**

| Event | Where it fires |
|---|---|
| `offers_scrolled` (`offset`) | `NotificationListener<ScrollEndNotification>` wrapping the list, `offset = metrics.pixels` |

No email or phone values are sent as properties.

## Deviations from a literal reading of the spec

The repo notes (`notes/posthog-free-tier-gone-in-days-an-event-per-keystroke.md`)
describe a quota blowout from capturing inside `onChanged` on every keystroke
and every slider step. A literal `onChanged` implementation would have repeated
that. So I used the patterns from that note:

- **Text fields:** the start events fire once per screen state, not per
  keystroke. The flags live on the registration screen's state, which persists
  while the offers route is on top, so "once" means once per registration
  screen lifetime, not once per navigation.
- **Slider:** `loan_amount_changed` fires on `onChangeEnd`. `onChanged` only
  updates the UI now.
- **Scroll:** `offers_scrolled` fires once per completed scroll, not on every
  scroll update.

Event names and properties are unchanged, so the funnels should still line up.
Only the firing frequency changed.

## Things to be aware of

- `registration_continue_tapped` fires only when the button is enabled. A tap
  on the disabled button does nothing, so it isn't counted. If product wants to
  count those taps too, the handler would need to move out of `onPressed`.
- `terms_accepted` fires every time the box is ticked. If someone unticks and
  re-ticks it, that counts twice. If product wants one event per user, add a
  flag like the text-field ones.
- `loan_amount_changed` fires on a tap on the slider as well as a drag, because
  `onChangeEnd` also runs after a tap. The value sent is the one the user
  landed on.

## Verification

- `flutter analyze lib`: no issues found.
- I did not run the app or check events in PostHog. `Analytics.init` still has
  the placeholder key `phc_REPLACE_ME_IN_CI`, so events will not reach a real
  project until that is set in CI.
- `flutter pub get` changed `analysis_options.yaml` and created `pubspec.lock`
  and `.dart_tool/`. I reverted and removed them, so the only changes are the
  two screen files and this file.
