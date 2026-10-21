# Analytics events from docs/EVENTS.md

I added all six events from `docs/EVENTS.md`. Each one goes through `Analytics.capture`. The names and properties match the spec exactly, so the dashboards and funnels that already exist keep working. No email or phone value is sent anywhere.

We are on PostHog's free tier, which is billed per event. So I chose *when* each event fires to avoid one event per keystroke, per slider step or per scroll frame (see `notes/posthog-free-tier-gone-in-days-an-event-per-keystroke.md`).

| Event | Where | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `onChanged` | Once per screen visit, on the first edit (`_emailStartedFired` flag) |
| `registration_phone_started` | phone `onChanged` | Once per screen visit, on the first edit (`_phoneStartedFired` flag) |
| `loan_amount_changed` `{amount: int}` | Slider `onChangeEnd` | Once per drag or tap, when the user lets go. `onChanged` still only updates the UI |
| `terms_accepted` | Checkbox `onChanged` | Only when the box is ticked, not when it is unticked |
| `registration_continue_tapped` `{amount: int, terms: bool}` | Continue button | Each tap, just before going to `/offers` |
| `offers_scrolled` `{offset: double}` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` around the list | Once per scroll gesture, when it settles. `offset` = `metrics.pixels` |

`amount` is sent as `_amount.round()` (an int), the same as the label shown on screen.

## Choices you may want to check
- "Once per visit" means per `RegistrationScreen` state. If the user goes back from Offers, the screen is still on the navigator stack, so the started events will not fire again.
- `terms_accepted` fires again if the user unticks and re-ticks the box. Continue can be tapped more than once if the user comes back. Both are rare, deliberate actions, so I did not add once-only flags. They would be easy to add if the funnel should count each user only once.

## Verification
- I ran `dart format lib` and `flutter analyze`: no issues.
- I did not run it on a device or emulator, and I sent nothing to PostHog.
- `flutter analyze` ran `pub get`, which downloaded packages from pub.dev and created `.dart_tool/` and `pubspec.lock`. I deleted both afterwards.
- During that run `analysis_options.yaml` also changed: an `analyzer.exclude` block appeared. That was not part of this task, so I put the file back the way it was.
