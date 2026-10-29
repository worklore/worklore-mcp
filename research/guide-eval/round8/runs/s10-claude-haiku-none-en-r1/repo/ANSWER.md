# Registration and offers analytics

Implemented the six events from `docs/EVENTS.md` on the two screens, using
`Analytics.capture` from `lib/analytics.dart`. Names and property keys match the
doc exactly.

## Changes

### `lib/screens/registration_screen.dart`

| Event | Where | Properties |
|---|---|---|
| `registration_email_started` | Email `onChanged`, first time the field becomes non-empty | — |
| `registration_phone_started` | Phone `onChanged`, first time the field becomes non-empty | — |
| `loan_amount_changed` | Slider `onChangeEnd` | `amount` (int) |
| `terms_accepted` | Checkbox `onChanged`, only when ticked (not unticked) | — |
| `registration_continue_tapped` | Continue button `onPressed`, before navigating | `amount` (int), `terms` (bool) |

### `lib/screens/offer_screen.dart`

| Event | Where | Properties |
|---|---|---|
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` around the list | `offset` (double, `metrics.pixels`) |

## Decisions I made (not specified in the doc)

- **`loan_amount_changed` fires on slider release, not on every drag tick.**
  The doc says "the chosen amount", so I used `onChangeEnd`. Using `onChanged`
  would send dozens of events per drag and skew the funnel.
- **"Started typing" = first non-empty value, once per screen visit.** Tracked
  with `_emailStarted` / `_phoneStarted` flags, so each fires at most once.
- **`terms_accepted` fires only on tick.** Unticking does not send an event.
- **`offers_scrolled` fires once per finished scroll**, not per frame. The list
  has no programmatic scrolling, so every `ScrollEndNotification` is user-driven.
- **No PII.** The email and phone values are never passed to any event.

## Verification

- `flutter analyze`: no issues found.
- `dart format`: the touched files are formatted.
- I did not run the app or send any events. Nothing was deployed or reported
  to PostHog or any other service.

## Things I noticed but did not change

- `lib/analytics.dart` still has the placeholder key `phc_REPLACE_ME_IN_CI`.
  Events will not reach PostHog until that is replaced (CI or config).
- `README.md` says the screens "do not send any of them yet". That is now
  out of date and could be updated.
- `flutter pub get` rewrote `analysis_options.yaml` (it added an `analyzer:
  exclude` block). I reverted that, along with the generated `.dart_tool/` and
  `pubspec.lock`, so the diff contains only the two screen files and this
  file.
