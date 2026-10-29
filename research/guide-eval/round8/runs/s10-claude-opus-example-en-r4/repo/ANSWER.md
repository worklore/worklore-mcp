# Analytics events from docs/EVENTS.md

All six events are sent through `Analytics.capture` (`lib/analytics.dart`). Names and properties are exactly as the spec gives them. No email or phone value is sent anywhere.

| Event | Where | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `onChanged` | Once, on the first non-empty edit (`_emailStartedFired` flag) |
| `registration_phone_started` | `registration_screen.dart`, phone `onChanged` | Once, on the first non-empty edit (`_phoneStartedFired` flag) |
| `loan_amount_changed` `{amount: int}` | Slider `onChangeEnd` | Once per drag or tap, when the user lets go. `onChanged` still only updates the UI |
| `terms_accepted` | Checkbox `onChanged` | Only when the box goes from unticked to ticked, not when it is unticked |
| `registration_continue_tapped` `{amount: int, terms: bool}` | Continue button | On tap, before navigating to `/offers` |
| `offers_scrolled` `{offset: double}` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` around the list | Once per scroll gesture, when it settles. `offset` = `metrics.pixels` |

Checks: `flutter analyze` reports no issues. I did not run the app on a device or emulator, so the PostHog debug-log check from the note has not been done.

## Which parts of the colleague's note applied

We are on the PostHog free tier and the spec wording ("started typing", "moved the slider", "scrolled") matches the note's case, so its main point applied. Wiring these to `onChanged` or to scroll updates would have sent one event per keystroke, slider step or scroll frame.

Applied:
- **Text fields:** a once-only flag in `onChanged`.
- **Slider:** the event moved to `onChangeEnd`.
- **Scroll:** `ScrollEndNotification`, not scroll updates or a `ScrollController` listener.
- **Names and properties** kept exactly as specified, so the existing dashboards and funnels keep working.
- **The note's caveat about state surviving navigation:** `RegistrationScreen` is the root route, so its state stays alive while `/offers` is pushed on top. This means "started" fires once per registration screen lifetime (per flow), not again every time the user comes back from offers. That matches a funnel step. If product wants it per visit, reset the flags when the route becomes visible again.

Did not apply:
- **Focus-lost capture:** no event needs a field's final value.
- **`FocusNode` tap events:** the spec has no tap/focus events.
- **posthog_flutter 5.x:** the note's version matches ours (`^5.36.0`), but nothing version-specific was needed.
- **Verification steps:** the `PostHogConfig.debug` run and the PostHog Activity check were not done (no device or external service used).

## Open points for product
- `terms_accepted` and `loan_amount_changed` can fire more than once per visit if the user unticks and re-ticks the box, or drags several times. Each is one event per deliberate action, so the volume is small. Add a once-only flag if the funnel should count only the first.
- `offers_scrolled` fires once per scroll gesture, with the position where that scroll ended. If you only want the deepest point reached, it could be sent once when the user leaves the screen instead.
