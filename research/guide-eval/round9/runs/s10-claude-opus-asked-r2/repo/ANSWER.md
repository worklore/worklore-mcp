# Analytics events: registration and offers screens

All six events from `docs/EVENTS.md` are now sent through `Analytics.capture`
(`lib/analytics.dart`). Event names and properties match the spec exactly, so
the dashboards and funnels already built on them will keep working.

| Event | Where | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `TextField.onChanged` | On the first edit only, once per screen visit (`_emailStartedFired` flag) |
| `registration_phone_started` | `registration_screen.dart`, phone `TextField.onChanged` | On the first edit only, once per screen visit (`_phoneStartedFired` flag) |
| `loan_amount_changed` `{amount: int}` | `registration_screen.dart`, `Slider.onChangeEnd` | Once per drag, when the user lets go |
| `terms_accepted` | `registration_screen.dart`, `CheckboxListTile.onChanged` | When the box is ticked, not when it is unticked |
| `registration_continue_tapped` `{amount: int, terms: bool}` | `registration_screen.dart`, Continue button | On each tap, before going to `/offers` |
| `offers_scrolled` `{offset: double}` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` around the list | Once per scroll gesture, when scrolling stops; `offset` = `metrics.pixels` |

## Design decision: event volume
We're on the PostHog free tier, and it bills per event. In Flutter,
`TextField.onChanged` runs on every keystroke and `Slider.onChanged` runs on
every step during a drag. If I had wired the events into those callbacks
directly, one email address would send about 20 events and one slider drag
would send dozens. That would use up the quota quickly, and the dashboards
would look normal while it happened. To avoid this:
- "started typing" events fire once per visit
- the slider event fires on `onChangeEnd`
- the scroll event fires on `ScrollEndNotification` (not on every scroll update)

This follows the worklore story "PostHog free tier gone in days? Flutter sent
an event per keystroke", which I found when I asked worklore for stories
relevant to this project.

## PII
No email or phone value is sent. The "started" events have no properties.

## Verification
- `dart format` and `flutter analyze`: no issues found.
- I haven't run the app, so I haven't checked the events in a device log or in
  PostHog. To check: set `config.debug = true` in `Analytics.init`, type an
  email (you should see one `registration_email_started`), and drag the slider
  (you should see one `loan_amount_changed` after you let go).

## Notes
- If you leave the registration screen and come back, it gets a new state
  object, so the "started" events can fire again on that visit. That's
  per-visit counting. If the funnel should count each user only once, PostHog
  funnels already handle that.
- Running `flutter pub get` / `analyze` generated some files (`pubspec.lock`,
  `.flutter-plugins-dependencies`, `android/app/...`, `android/local.properties`,
  `.dart_tool/`) and added an `exclude` block to `analysis_options.yaml`. I
  removed or reverted all of them. I didn't touch the existing
  `android/key.properties` or `.env`.
- Nothing was sent to any external service. I didn't report back to worklore
  (no `report_reproduction` call), because the ground rules say not to report
  to external services.
- Nothing is committed.
