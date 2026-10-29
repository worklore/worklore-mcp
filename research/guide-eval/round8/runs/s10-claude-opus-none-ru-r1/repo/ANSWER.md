# Analytics events from docs/EVENTS.md

All six events are sent through `Analytics.capture` (`lib/analytics.dart`).
The wrapper, `main.dart` and the PostHog config are unchanged. Event names
match `docs/EVENTS.md` exactly.

## Registration screen (`lib/screens/registration_screen.dart`)

| Event | Where | Properties |
|---|---|---|
| `registration_email_started` | Email field `onChanged`, the first time it becomes non-empty | — |
| `registration_phone_started` | Phone field `onChanged`, the first time it becomes non-empty | — |
| `loan_amount_changed` | Slider `onChangeEnd` | `amount`: `int` (`_amount.round()`) |
| `terms_accepted` | Checkbox `onChanged`, only when it is ticked (not when unticked) | — |
| `registration_continue_tapped` | Continue button, before navigating to `/offers` | `amount`: `int`, `terms`: `bool` |

## Offers screen (`lib/screens/offer_screen.dart`)

| Event | Where | Properties |
|---|---|---|
| `offers_scrolled` | `ScrollEndNotification` around the `ListView` | `offset`: `double` (`metrics.pixels`) |

`OfferScreen` became a `StatefulWidget` so it can remember the deepest offset
already sent.

## Choices I made

We are on the PostHog free tier, so I avoided sending an event on every
keystroke or every frame:

- **Started typing**: one event per field per screen visit, with flags
  `_emailStarted` / `_phoneStarted`. It does not fire again if the user
  clears the field and types again.
- **Amount**: `onChangeEnd`, not `onChanged`. That gives one event per drag or
  tap with the final value, instead of dozens per drag.
- **Scroll**: sent when a scroll gesture ends, and only if the user got
  further down than any offset already sent on this visit. Scrolling back up
  sends nothing. `offset` is how far down they got.
- **PII**: no email or phone values are sent. The "started" events have no
  properties.

If product wants different behaviour (for example, an event on every scroll
end, or `terms_accepted` firing again after untick and re-tick), it's a
one-line change in each place.

## Checks

- `dart format lib` and `flutter analyze` report no issues.
- `flutter analyze` ran `pub get`, which created `.dart_tool/` and
  `pubspec.lock` and changed `analysis_options.yaml`. I reverted and deleted
  all of these so only the two screens and this file changed.
- No tests exist in the project and I didn't add any. I didn't run the app on
  a device, so nothing went to PostHog.
