# Registration funnel events

I added all six events from `docs/EVENTS.md`. Every one goes through
`Analytics.capture`, and the names match the spec exactly. I changed only
`lib/screens/registration_screen.dart` and `lib/screens/offer_screen.dart`.

| Event | Where / trigger | Properties |
|---|---|---|
| `registration_email_started` | Email field `onChanged`, the first time it's non-empty | — |
| `registration_phone_started` | Phone field `onChanged`, the first time it's non-empty | — |
| `loan_amount_changed` | Slider `onChangeEnd` | `amount`: `int` (`v.round()`) |
| `terms_accepted` | Checkbox goes from unticked to ticked | — |
| `registration_continue_tapped` | Continue button, before going to `/offers` | `amount`: `int`, `terms`: `bool` |
| `offers_scrolled` | `ScrollEndNotification` on the offers list | `offset`: `double` (pixels) |

## Limiting event volume (we're on the PostHog free tier)

Several of these callbacks fire far more often than the event they stand for.
Sending an event on every call would use up the free-tier quota and make the
funnel numbers hard to read:

- **Email / phone started**: `onChanged` fires on every keystroke. Each event
  is sent once per visit to the registration screen, the first time the field
  has text in it.
- **Loan amount**: a slider's `onChanged` fires on every frame of a drag. I
  used `onChangeEnd` instead, so one drag or tap sends one event with the
  amount the user ended on.
- **Terms**: sent only when the box is ticked, not when it's unticked. If the
  user unticks and ticks again, it's sent again.
- **Offers scrolled**: scroll notifications fire on every frame. The event is
  sent when a scroll gesture ends (top-level list only, `depth == 0`), and
  only if the user is further down than the last offset sent on that visit.
  So `offset` is the deepest point reached so far, and scrolling back up
  sends nothing.
  `OfferScreen` was a `StatelessWidget`. I made it a `StatefulWidget` so it
  can remember that deepest offset.

## PII

No email or phone number is sent. The "started" events have no properties,
and the email/phone values never go into any event.

## Things to know

- `registration_continue_tapped.terms` will always be `true`, because the
  Continue button is disabled until terms are accepted (`_canContinue`). I
  send it anyway because the spec lists it.
- Screen views were already tracked by `PosthogObserver`, so I didn't add any.

## Checks

- `dart format lib` and `flutter analyze` both pass with no issues.
  `flutter_lints` couldn't be resolved locally, because `pub get` didn't
  finish in this environment. So the analysis ran without the lint rule set,
  only the analyzer's default checks.
- Running the Flutter tools added an `analyzer.exclude` block to
  `analysis_options.yaml` and created `.dart_tool/` and `pubspec.lock`. I
  reverted all three, since they aren't part of this change.
- No tests exist and I didn't run the app. Nothing was sent to PostHog or any
  other external service.
