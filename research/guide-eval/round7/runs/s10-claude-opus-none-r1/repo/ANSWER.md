# Analytics events from docs/EVENTS.md

All six events are sent through `Analytics.capture` (`lib/analytics.dart`). Event
names and property names match the spec exactly. I didn't change `analytics.dart`,
`main.dart` or the PostHog config.

## Where each event fires

| Event | File | Trigger | Properties |
|---|---|---|---|
| `registration_email_started` | `registration_screen.dart` | First non-empty `onChanged` of the email field | — |
| `registration_phone_started` | `registration_screen.dart` | First non-empty `onChanged` of the phone field | — |
| `loan_amount_changed` | `registration_screen.dart` | Slider `onChangeEnd`, only if the value changed during the drag | `amount` (int) |
| `terms_accepted` | `registration_screen.dart` | Checkbox goes from unticked to ticked (not when unticked) | — |
| `registration_continue_tapped` | `registration_screen.dart` | Continue button tap, before navigating | `amount` (int), `terms` (bool) |
| `offers_scrolled` | `offer_screen.dart` | `ScrollEndNotification` on the list, only when the offset is further than any earlier report | `offset` (double, pixels) |

## Decisions worth reviewing

The raw Flutter callbacks fire far more often than the spec intends. Sending
every one of them would flood the funnel and burn through the PostHog free-tier
event quota. So I limited them like this:

- **Email/phone "started"**: `onChanged` runs on every keystroke. These events
  fire **once per visit to the registration screen**, on the first character typed.
- **Loan amount**: the slider's `onChanged` fires on every frame of a drag. I
  used `onChangeEnd` instead, so one drag sends one event with the final
  amount. A drag that ends where it started sends nothing.
- **Offers scrolled**: scroll notifications arrive every frame. The event fires
  only when a scroll gesture ends, and only if the user got further down than
  before. Each event is therefore a new "deepest point reached", and scrolling
  back up sends nothing. If product wants every scroll gesture instead, remove
  the `_maxReportedOffset` check.
- **Terms accepted**: fires each time the box is ticked. Unticking sends nothing.
- **PII**: no email or phone values are sent. The "started" events have no
  properties.
- `terms` in `registration_continue_tapped` will always be `true` in practice,
  because Continue is disabled until the terms are accepted. It's sent anyway
  because the spec lists it.
- `OfferScreen` became a `StatefulWidget` so it can remember the deepest offset
  it has already reported.

## Verification

- `flutter analyze` reports no issues.
- Not run on a device or emulator, and no events were sent to PostHog. There are
  no tests in the repo, and I didn't add any.
- Running `flutter analyze` made the Flutter SDK rewrite `analysis_options.yaml`
  on its own (it added build/platform excludes). I reverted that and deleted the
  generated `.dart_tool/` and `pubspec.lock`. The only changes are the two
  screen files and this file.
