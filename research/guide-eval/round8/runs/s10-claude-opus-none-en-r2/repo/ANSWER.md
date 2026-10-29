# Analytics events: registration and offers screens

All six events from `docs/EVENTS.md` are now sent through `Analytics.capture`.
Names and property types match the spec exactly. No email or phone value is
sent anywhere.

| Event | Where | How it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `onChanged` | Once per screen visit, on the first non-empty input |
| `registration_phone_started` | `registration_screen.dart`, phone `onChanged` | Once per screen visit, on the first non-empty input |
| `loan_amount_changed` | `registration_screen.dart`, `Slider.onChangeEnd` | Once per drag or tap, when the user lets go. `amount` is an int (`_amount.round()`) |
| `terms_accepted` | `registration_screen.dart`, checkbox `onChanged` | Only when the box gets ticked. Unticking sends nothing |
| `registration_continue_tapped` | `registration_screen.dart`, Continue button | Before navigating to `/offers`. Sends `amount` (int) and `terms` (bool) |
| `offers_scrolled` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` | When a scroll gesture stops, and only if the user is further down than before on this visit. `offset` is a double (pixels) |

## Choices I made (please check)

- **Event volume (we're on the PostHog free tier).** If the spec were taken
  literally ("moved the slider", "scrolled"), `onChanged` and every scroll
  update would send dozens of events per gesture. So:
  - the slider sends only on release (`onChangeEnd`),
  - "started typing" fires once per visit, not on every keystroke,
  - scroll sends only when a gesture ends and reaches a new furthest point.
    So `offset` is how far down the user has got so far, and the largest value
    in a session is their deepest scroll.
- **`terms` on Continue is always `true`**, because the button is disabled
  until terms are accepted. I still send it, as the spec asks for it.
- To track scroll depth, `OfferScreen` is now a `StatefulWidget`. The UI did
  not change.

## Verification

- Ran `dart format` and `flutter analyze` with no issues. I didn't run the app
  on a device and didn't check that events show up in PostHog. Nothing was
  sent to any external service.
- The Flutter tooling (`pub get` and `analyze`) kept adding an `analyzer.exclude` block to
  `analysis_options.yaml`. I reverted it and deleted the generated
  `.dart_tool/` and `pubspec.lock`.
