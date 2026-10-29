# Analytics events from docs/EVENTS.md

All six events are now sent through `Analytics.capture` (`lib/analytics.dart`).
Event names and properties are exactly as written in the spec. `lib/analytics.dart`
and `lib/main.dart` are unchanged.

| Event | Where | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `TextField.onChanged` | On the first edit only, guarded by `_emailStartedFired`. No properties, so the email is never sent. |
| `registration_phone_started` | phone `TextField.onChanged` | On the first edit only, guarded by `_phoneStartedFired`. The phone number is never sent. |
| `loan_amount_changed` `{amount: int}` | `Slider.onChangeEnd` | Once per drag or tap, when the user lets go. Skipped if the value is the same as at `onChangeStart`, e.g. after tapping the thumb without moving it. `onChanged` now only updates the UI. |
| `terms_accepted` | `CheckboxListTile.onChanged` | When the box changes to ticked. Unticking sends nothing. |
| `registration_continue_tapped` `{amount: int, terms: bool}` | Continue button `onPressed` | On each tap, before navigating to `/offers`. |
| `offers_scrolled` `{offset: double}` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` around the list | Once per scroll gesture, when scrolling stops. `offset` is `metrics.pixels`. Only the list's own scrolls count (`depth == 0`). |

Verification: `flutter analyze` reports no issues. I did not run the app on a
device or emulator, and I did not check the events in PostHog.

## Which parts of the colleague's note applied

This app has the same setup as the note: Flutter, `posthog_flutter` 5.x, and
the PostHog free tier, which bills per event (see README). Its spec also uses
the same wording ("started typing", "moved the slider", "scrolled"). The
screens had no events yet, so there was nothing to fix. I used the note's
approach when writing the code, so the problem never appears:

- **Applied: once-per-visit flags for text fields.** Both `*_started` events
  use a `bool` flag, so each one fires once, not on every keystroke.
- **Applied: `onChangeEnd` for the slider.** Without it, one drag across the
  49 divisions could send dozens of `loan_amount_changed` events.
- **Applied: `ScrollEndNotification` instead of scroll updates** for
  `offers_scrolled`.
- **Applied: keep names and properties unchanged.** The dashboards depend on them.
- **Not needed: firing on focus loss and `FocusNode` tap events.** No event in
  the spec needs a field's final value, and no event is about tapping a field.
  Also, email and phone are PII and must not be sent at all.
- **Not used: the note's verification steps** (`PostHogConfig.debug`, PostHog →
  Activity). They need a running app and the PostHog dashboard, and I used
  neither.

## Things to know / open choices

- **"Once" means once per lifetime of the registration screen's state.** That
  state stays alive while `/offers` is open on top of it. So if a user goes
  back and edits the email again, `registration_email_started` is not sent a
  second time. For a funnel that is probably what you want. If you want one
  event per visit instead, reset the flags when the user returns to the screen.
- **`offers_scrolled` fires once per scroll gesture, not once per visit.**
  This keeps the offset data useful. If you only need it as a funnel step,
  adding a once-per-visit flag would cut the volume further.
- **`terms_accepted` fires again if the user unticks and ticks again.** This is
  rare and cheap. Add a flag if you want it to fire only once.
