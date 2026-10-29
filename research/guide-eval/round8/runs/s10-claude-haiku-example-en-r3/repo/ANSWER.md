# Analytics events: registration and offers screens

Implemented every event in `docs/EVENTS.md` through the existing `Analytics.capture`
wrapper. Event names and properties match the spec exactly.

## What changed

**`lib/screens/registration_screen.dart`**

| Event | Where it fires |
|---|---|
| `registration_email_started` | Email field `onChanged`, once per screen visit (guarded by `_emailStarted`) |
| `registration_phone_started` | Phone field `onChanged`, once per screen visit (guarded by `_phoneStarted`) |
| `loan_amount_changed` `{amount}` | Slider `onChangeEnd`, once when the user lets go. `onChanged` still only updates the UI. |
| `terms_accepted` | Checkbox `onChanged`, when the box becomes ticked |
| `registration_continue_tapped` `{amount, terms}` | Continue button `onPressed`, before navigating to `/offers` |

**`lib/screens/offer_screen.dart`**

| Event | Where it fires |
|---|---|
| `offers_scrolled` `{offset}` | `NotificationListener<ScrollEndNotification>` wrapping the list. `offset` is `metrics.pixels`. Returns `false` so the notification keeps bubbling. |

**`README.md`**: The line saying the screens send no events was out of date, so I updated it.

## Choices I made

- **Once per visit for the "started" events.** The spec says "started typing", and the
  `onChanged` callback fires on every keystroke. The flags live on the screen state, so each
  new visit to the registration screen can fire them again.
- **`loan_amount_changed` on `onChangeEnd`, not `onChanged`.** The spec says "moved the slider",
  and a drag would otherwise send dozens of events. This sends one event per interaction.
  The amount is the value at release, which is the chosen amount.
- **`terms_accepted` fires on every tick to true.** A tick is a discrete tap, not a stream,
  so I did not add a once-only flag. Untick and re-tick will send a second event.
- **`offers_scrolled` on `ScrollEndNotification`.** The spec has no per-update requirement,
  and `ScrollUpdateNotification` would fire many times per swipe.
- **No PII.** The email and phone values are never sent. The "started" events carry no properties.
- **`registration_continue_tapped` is only reachable when enabled.** The button is disabled
  unless terms are ticked, so `terms` is always `true` when the event fires. I still send the
  real value, as the spec asks.

## Colleague's note: what applied

The note is a case study from a different app. I used the parts that matched this code:

- **Applied:** Text fields fire once per visit with a `bool` flag, rather than on every
  `onChanged`.
- **Applied:** Slider capture moved from `onChanged` to `onChangeEnd`. `onChanged` stays for the UI.
- **Applied:** Scroll capture uses `ScrollEndNotification`, not per-update notifications.
- **Applied:** Event names and properties are unchanged, so existing funnels keep working.
- **Not applicable:** Focus-lost capture for events that need the final field value. No event
  in this spec needs the final value, so I did not add focus listeners.
- **Not applicable:** Verifying in a debug build with `PostHogConfig.debug = true`. The config
  key is a placeholder (`phc_REPLACE_ME_IN_CI`), and running the app would send events to the
  external PostHog service. I did not do that.

## Verification

- `flutter analyze`: no issues found.
- `dart format --set-exit-if-changed lib`: passes, no files changed.
- Not run on a device or simulator, so I have not seen the events arrive in PostHog. Check in
  PostHog → Activity that each event fires once per interaction, and that the slider fires
  once per drag.
- Unverified assumption: Flutter's `Slider.onChangeEnd` also fires on a plain tap, not only
  after a drag. I believe it does, so a tap on the track should also send one
  `loan_amount_changed`. Confirm on a device.

Tooling side effects were reverted. `flutter pub get` rewrote `analysis_options.yaml` and created
`pubspec.lock` and `.dart_tool/`. I restored the file and removed the generated files, so the
diff contains only the changes above, plus `ANSWER.md`.
