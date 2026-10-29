# Analytics events from docs/EVENTS.md

I added all six events from `docs/EVENTS.md`. Each one is sent through `Analytics.capture`, and the names match the spec exactly.

| Event | Where | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `onChanged` | The first time the field has text. Once per visit to the screen. |
| `registration_phone_started` | `registration_screen.dart`, phone `onChanged` | The first time the field has text. Once per visit to the screen. |
| `loan_amount_changed` `{amount: int}` | Slider `onChangeEnd` | When the user lets go of the slider, with the rounded amount. |
| `terms_accepted` | Checkbox `onChanged` | Only when the box becomes ticked, not when it is unticked. |
| `registration_continue_tapped` `{amount: int, terms: bool}` | Continue button | When the button is tapped, just before going to `/offers`. |
| `offers_scrolled` `{offset: double}` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` around the list | Each time a scroll comes to rest, with `metrics.pixels`. |

## Decisions worth knowing
- **Keeping the event count low.** We're on the PostHog free tier, so I avoided
  sending an event for every UI callback:
  - The "started" events fire once, not on every keystroke.
  - The slider uses `onChangeEnd` instead of `onChanged`, because `onChanged` fires on every frame of a drag.
  - The scroll event fires once per scroll gesture, not on every scroll update.
- **No personal data.** The email and phone text are never sent. Only the event names and the listed properties go out.
- **`terms` on continue** is always `true` in practice. The button only works once terms are ticked, but the spec asks for the property, so it's included.
- **`offers_scrolled` may be rare.** There are only 10 offers. On tall screens the list may not scroll at all, so this funnel step could look smaller than it really is.
- **No new screen-view events.** Screen views are still handled by `PosthogObserver`, as the spec says.

## Checks
- I ran `dart format` and `flutter analyze` and got no issues.
- I did not run the app or any tests (the repo has none), so nothing was sent to PostHog.
- `flutter analyze` rewrote `analysis_options.yaml` by itself to add exclude paths. I put that file back. I also deleted the `pubspec.lock` and `.dart_tool/` created by `flutter pub get`, so the only files changed are the two screens and this one.
