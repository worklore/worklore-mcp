# Analytics events: what I did

I added all six events from `docs/EVENTS.md`. Each one goes through `Analytics.capture` (`lib/analytics.dart`). The event names and property names match the spec exactly. Only two files changed: `lib/screens/registration_screen.dart` and `lib/screens/offer_screen.dart`.

| Event | Where / trigger | Properties |
|---|---|---|
| `registration_email_started` | Email `TextField.onChanged`, **first keystroke only** per screen visit | — |
| `registration_phone_started` | Phone `TextField.onChanged`, **first keystroke only** per screen visit | — |
| `loan_amount_changed` | `Slider.onChangeEnd` (when the user lets go of the slider) | `amount`: int (`_amount.round()`) |
| `terms_accepted` | `CheckboxListTile.onChanged`, only when the box becomes **ticked** (unticking sends nothing) | — |
| `registration_continue_tapped` | Continue button, sent just before navigating to `/offers` | `amount`: int, `terms`: bool |
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` around the offers list | `offset`: double (`metrics.pixels`) |

## Decisions worth reviewing

The spec says *when* each event happens but not how often it should fire. Since we're on the PostHog free tier and the events feed funnels, I kept the volume to one meaningful event per user action:

- **"Started typing" fires once per visit, not on every keystroke.** It's tracked with `_emailStarted` and `_phoneStarted` flags in the screen state. If the user leaves the screen and comes back, it fires again.
- **The slider uses `onChangeEnd`, not `onChanged`.** `onChanged` fires on every frame of a drag, which would mean dozens of events per drag with in-between amounts. `onChangeEnd` sends the amount the user actually chose.
- **Scrolling uses `ScrollEndNotification`.** It sends one event per scroll gesture, after any fling has stopped, with the final offset. Listening to raw scroll updates would send an event every frame.
- **`terms_accepted` only fires on tick.** The spec says "ticked", so unticking is not tracked. Ticking, unticking and ticking again sends the event twice.
- **No PII.** No event includes the email or phone text. The text-field events send no properties at all.
- **No screen-view events added.** `PosthogObserver` already tracks those, as the spec notes.

## Verification

- `dart format lib` was applied, and `flutter analyze` reports **No issues found**.
- Running `flutter analyze` also ran `pub get`, which created `.dart_tool/` and `pubspec.lock` and rewrote `analysis_options.yaml`. I reverted or removed all three, so the diff only contains the two screen files.
- I did not run the app and did not send any events to PostHog. There are no tests in the repo and I didn't add any. To check by hand, run the app against a dev PostHog project, or put a `debugPrint` in `Analytics.capture`.
