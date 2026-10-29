# Registration and offers analytics

Implemented all six events from `docs/EVENTS.md` using `Analytics.capture`.
Only the two screen files changed.

## What was added

| Event | Where | Trigger | Properties |
|---|---|---|---|
| `registration_email_started` | `registration_screen.dart` | First non-empty value in the email field, once per screen visit | — |
| `registration_phone_started` | `registration_screen.dart` | First non-empty value in the phone field, once per screen visit | — |
| `loan_amount_changed` | `registration_screen.dart` | Slider drag ends (`onChangeEnd`) | `amount` (int) |
| `terms_accepted` | `registration_screen.dart` | Checkbox goes from unticked to ticked | — |
| `registration_continue_tapped` | `registration_screen.dart` | Continue tapped (only fires when the button is enabled) | `amount` (int), `terms` (bool) |
| `offers_scrolled` | `offer_screen.dart` | Scroll ends (`ScrollEndNotification`) | `offset` (double, `metrics.pixels`) |

## Choices I made

- **Once-per-visit for the "started" events.** `registration_email_started` and
  `registration_phone_started` use a flag, so they fire only on the first
  character typed, not on every keystroke. The doc says "started typing", which
  reads as once.
- **`loan_amount_changed` fires on drag end, not on every slider tick.**
  `onChanged` fires many times per drag. The doc says "the chosen amount", so I
  sent the final value once. If the funnel needs every intermediate move, switch
  `onChangeEnd` to `onChanged`.
- **`offers_scrolled` fires on scroll end, not on every scroll update.** Same
  reasoning: the offset at which the scroll stopped is one event per scroll.
  It is wrapped in a `NotificationListener`, so the `OfferScreen` widget stays a
  `StatelessWidget`.
- **`terms_accepted` fires only on tick, not on untick.** The doc describes
  acceptance.
- **No PII.** Email and phone values are never sent. The handlers only check
  whether the field is empty.

## Verification

- `flutter analyze` reports "No issues found!".
- I did not run the app or exercise the events on a device or simulator, so the
  PostHog side is unverified. The `phc_REPLACE_ME_IN_CI` key in `analytics.dart`
  is untouched, and nothing was sent to PostHog or any other service.

## Side effects I cleaned up

Running `flutter analyze` rewrote `analysis_options.yaml` (it added an analyzer
exclude block) and created `pubspec.lock` and `.dart_tool/`. I reverted the
YAML file and deleted the two generated items. Only the two screen files and
this file differ from the original commit.
