# Analytics events — what was done

All six events from `docs/EVENTS.md` are now sent through `Analytics.capture`
(`lib/analytics.dart`). Event names and property names/types match the spec exactly.

| Event | Where | Fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `TextField.onChanged` | once per screen visit, on the first edit |
| `registration_phone_started` | `registration_screen.dart`, phone `TextField.onChanged` | once per screen visit, on the first edit |
| `loan_amount_changed` `{amount: int}` | `registration_screen.dart`, `Slider.onChangeEnd` | once per drag, when the user lets go |
| `terms_accepted` | `registration_screen.dart`, checkbox `onChanged` | once per visit, the first time the box is ticked (unticking does nothing) |
| `registration_continue_tapped` `{amount: int, terms: bool}` | `registration_screen.dart`, Continue button | every tap, before navigating to `/offers` |
| `offers_scrolled` `{offset: double}` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` around the list | once per scroll gesture, when scrolling stops; `offset` = `metrics.pixels` |

## Why the events fire this way
We're on the PostHog free tier, which is billed per event. In Flutter,
`TextField.onChanged` runs on every keystroke, `Slider.onChanged` runs on every
step of a drag, and scroll updates fire every frame. Putting `capture` there
would send dozens of events per user and use up the quota quickly. So:
- the "started" events and `terms_accepted` are protected by once-per-visit `bool` flags on the screen state,
- the slider event uses `onChangeEnd` (`onChanged` still updates the UI),
- the scroll event listens for `ScrollEndNotification` (with `depth == 0`, so only the list itself counts).

I took this approach from a worklore story ("PostHog free tier gone in days?
Flutter sent an event per keystroke"). I did not send a reproduction report
back to worklore, because the ground rules forbid reporting to external services.

## PII
No email or phone value is sent. The text-field events have no properties.

## Verification
- `dart format` and `flutter analyze`: no issues.
- I did not run the app, so I haven't checked the events in PostHog. To check: set
  `config.debug = true` in `Analytics.init`, run a debug build, type into the
  fields and drag the slider. Each "started" event should be logged once, and
  `loan_amount_changed` once per drag.
- `flutter pub get` created `pubspec.lock` and other generated files, and changed
  `analysis_options.yaml`. I removed or reverted all of them so the diff only
  touches the two screens and this file.

## Open points for product
- `terms_accepted` and the "started" events are counted per screen visit. If the
  user leaves the registration screen and comes back to a new screen instance,
  they can fire again.
- `offers_scrolled` fires on every scroll stop, not once per visit, so
  `offset` shows how far the user got each time. If the funnel only needs one
  per visit, it's a one-line flag like the others.
