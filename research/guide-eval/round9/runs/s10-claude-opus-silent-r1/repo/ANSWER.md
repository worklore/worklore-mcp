# Analytics events: registration and offers

I added all six events from `docs/EVENTS.md`. Every one goes through `Analytics.capture` (`lib/analytics.dart`), and the names match the spec exactly.

| Event | Where | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email field `onChanged` | On the first non-empty keystroke, once per screen visit |
| `registration_phone_started` | `registration_screen.dart`, phone field `onChanged` | On the first non-empty keystroke, once per screen visit |
| `loan_amount_changed` `{amount: int}` | `Slider.onChangeEnd` | Once per drag or tap, with the final rounded amount |
| `terms_accepted` | `CheckboxListTile.onChanged` | Only when the box goes from unticked to ticked (unticking sends nothing) |
| `registration_continue_tapped` `{amount: int, terms: bool}` | Continue button, just before navigating | Each tap |
| `offers_scrolled` `{offset: double}` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` | Once per visit, when the user's first scroll comes to rest with an offset above 0 |

## Choices I made
- **Fewer events.** We are on the PostHog free tier, and the spec describes a funnel, which only needs one event per step. Firing on every change would flood the dashboards:
  - The slider's `onChanged` and scroll notifications run on every frame, so I used `onChangeEnd` and `ScrollEndNotification` instead.
  - The "started" events and `offers_scrolled` are sent once per screen visit.
- **`offers_scrolled` offset.** The offset is where the first scroll stopped, not the furthest point reached. If product wants the maximum depth, the event would have to be sent when the screen closes (`dispose`). That would be lost if the app is killed, which is why I didn't do it.
- **No personal data.** The email and phone values are never sent; the events only record that typing started.
- **`terms` is always `true` in practice.** Continue is only enabled once terms are accepted, so the property is sent as the spec asks but will always be `true`.
- `OfferScreen` was turned into a `StatefulWidget` to hold the once-per-visit flag.

## Checks
- `dart format lib` and `flutter analyze` both pass with no issues.
- There are no tests in the repo and I didn't run the app, so the events haven't been checked against a live PostHog project.
- `flutter pub get` and `flutter analyze` created some files (`pubspec.lock`, `.flutter-plugins-dependencies`, `android/local.properties`, `android/app/...GeneratedPluginRegistrant.java`) and rewrote `analysis_options.yaml`. I removed the files and restored `analysis_options.yaml`. The only changes left are in the two screen files and this one. I did not touch `android/key.properties`, which was already there.

Nothing was deployed, published or sent to any outside service.

## Worth flagging (not changed)
`README.md` contains what looks like a real partner-bank sandbox API key in plain text (`KREDITO_PARTNER_API_KEY=...`), and it is committed to git. Consider replacing it with a placeholder and rotating the key.
