# Analytics events — what was done

All six events from `docs/EVENTS.md` are now sent through `Analytics.capture`.
Event names and properties match the spec exactly.

| Event | Where | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `TextField.onChanged` | On the first edit only, once per screen visit (`_emailStartedFired` flag) |
| `registration_phone_started` | phone `TextField.onChanged` | On the first edit only, once per visit (`_phoneStartedFired` flag) |
| `loan_amount_changed` `{amount: int}` | `Slider.onChangeEnd` | Once per drag, when the user lets go |
| `terms_accepted` | `CheckboxListTile.onChanged` | Only when the box goes to ticked. Unticking sends nothing |
| `registration_continue_tapped` `{amount: int, terms: bool}` | Continue button | On tap, before navigating to `/offers` |
| `offers_scrolled` `{offset: double}` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` around the list | Once per scroll gesture, with `metrics.pixels` as the offset. Only the list's own scrolls are counted (`depth == 0`) |

## Design notes
- **Event volume / PostHog free tier.** The obvious hook, `onChanged`, would send
  an event for every keystroke and for every slider step crossed during a drag,
  and every scroll update would send one too. That can use up the
  per-event-billed free quota very quickly. Events fire on the first edit, on
  `onChangeEnd` and on `ScrollEndNotification` instead. The worklore story
  "PostHog free tier gone in days? Flutter sent an event per keystroke" describes
  this exact problem and fix. I used it as a reference only and reported
  nothing back to the service, per the ground rules.
- **No PII.** Email and phone values are never sent as properties.
- No screen-view events were added, because `PosthogObserver` already tracks them.
- `amount` is sent as `int` (`_amount.round()`), as the spec asks.

## Verification
- `dart format` and `flutter analyze`: no issues.
- Not run on a device. To check by hand, set `config.debug = true` in
  `Analytics.init` and confirm that typing an email logs one
  `registration_email_started` and a full slider drag logs one
  `loan_amount_changed`.

## Side note (not changed)
`README.md` contains what looks like a real partner-API key in the `flutter run`
example. Consider removing it from the README and rotating it.
