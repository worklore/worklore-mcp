# Analytics events from docs/EVENTS.md

All six events are implemented. Each one is sent through `Analytics.capture`
(`lib/analytics.dart`), and the names match the spec exactly. I didn't change
`analytics.dart` or `main.dart`.

## Registration screen: `lib/screens/registration_screen.dart`

| Event | Where | Properties |
|---|---|---|
| `registration_email_started` | `onChanged` of the Email field, first character only | none |
| `registration_phone_started` | `onChanged` of the Phone field, first character only | none |
| `loan_amount_changed` | `Slider.onChangeEnd` (when the user lets go of the slider) | `amount`: `int` (`_amount.round()`) |
| `terms_accepted` | Checkbox `onChanged`, only when the box is ticked | none |
| `registration_continue_tapped` | `FilledButton.onPressed`, before navigating to `/offers` | `amount`: `int`, `terms`: `bool` |

## Offers screen: `lib/screens/offer_screen.dart`

`OfferScreen` is now a `StatefulWidget`, and the `ListView` is wrapped in a
`NotificationListener<ScrollNotification>`.

| Event | Where | Properties |
|---|---|---|
| `offers_scrolled` | `ScrollEndNotification` of the list | `offset`: `double` (`metrics.pixels`) |

## Choices I made (the spec didn't settle these)

Without throttling, the slider and the scroll would send dozens of events
every second. We're on the PostHog free tier, which has an event limit, and
the funnel only needs to know that the action happened. So:

- **Email/phone started** goes out once per screen visit, on the first
  character typed, not on every keystroke.
- **loan_amount_changed** fires on `onChangeEnd` instead of `onChanged`.
  That's one event per drag (or tap), with the final amount.
- **terms_accepted** fires only when the box is ticked (`true`). Unticking
  sends nothing, because the spec has no event for it.
- **offers_scrolled** fires when a scroll gesture ends, and only if the user
  went further down than the deepest point already sent. `offset` is how far
  down the list they got. Scrolling back up sends nothing.

## PII

The email and phone number are never sent. The email/phone events have no
properties, and `registration_continue_tapped` carries only `amount` and
`terms`.

## Checks

- `dart format lib`: formatted.
- `flutter analyze`: `No issues found!` (I ran `flutter pub get` first to
  download the dependencies).
- `flutter pub get` modified `analysis_options.yaml` on its own (it added
  `exclude` rules). I reverted that change and deleted the generated
  `.dart_tool/` and `pubspec.lock`, so the diff only touches the two screens.
- I didn't run the app on a device and there are no tests, so I haven't
  confirmed that events actually reach PostHog. Nothing was deployed or
  published.
