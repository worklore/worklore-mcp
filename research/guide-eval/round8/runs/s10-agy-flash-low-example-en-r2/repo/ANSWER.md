# Analytics Implementation Summary

## Implementation Details

All events defined in `docs/EVENTS.md` were implemented using the existing `Analytics` wrapper (`Analytics.capture(...)`) across the registration and offers screens:

1. **`registration_email_started`** ([lib/screens/registration_screen.dart](file:///tmp/h-HnIqak/lib/screens/registration_screen.dart))
   - Tracked when the user starts typing in the email field.
   - Guarded by a state flag `_emailStartedFired` so it fires only once per screen visit on the first keystroke without tracking on every subsequent keystroke.
   - No PII (email address) is captured.

2. **`registration_phone_started`** ([lib/screens/registration_screen.dart](file:///tmp/h-HnIqak/lib/screens/registration_screen.dart))
   - Tracked when the user starts typing in the phone number field.
   - Guarded by a state flag `_phoneStartedFired` so it fires only once per screen visit on the first keystroke.
   - No PII (phone number) is captured.

3. **`loan_amount_changed`** ([lib/screens/registration_screen.dart](file:///tmp/h-HnIqak/lib/screens/registration_screen.dart))
   - Tracked on the loan amount slider via `onChangeEnd` with property `amount: v.round()` (`int`).
   - Fires once when the user finishes dragging/releases the slider, rather than sending dozens of events on every micro-step during `onChanged`.

4. **`terms_accepted`** ([lib/screens/registration_screen.dart](file:///tmp/h-HnIqak/lib/screens/registration_screen.dart))
   - Tracked when the terms and conditions checkbox changes to checked (`newValue && !_terms`).

5. **`registration_continue_tapped`** ([lib/screens/registration_screen.dart](file:///tmp/h-HnIqak/lib/screens/registration_screen.dart))
   - Tracked in the Continue button `onPressed` callback when valid.
   - Includes properties: `amount` (`int`, `_amount.round()`) and `terms` (`bool`, `_terms`).

6. **`offers_scrolled`** ([lib/screens/offer_screen.dart](file:///tmp/h-HnIqak/lib/screens/offer_screen.dart))
   - Tracked using a `NotificationListener<ScrollEndNotification>` wrapping the offers `ListView.builder`.
   - Fires once when scrolling comes to an end, with property `offset: notification.metrics.pixels` (`double`), rather than spamming events on continuous scroll updates.

---

## Notes on Colleague's Note

The colleague's note described best practices for avoiding event quota exhaustion in Flutter when instrumenting analytics:

### Which parts applied:
- **Text fields (once-per-visit flag):** Applied to `registration_email_started` and `registration_phone_started`. Instead of emitting an event on every keystroke in `onChanged`, boolean flags (`_emailStartedFired`, `_phoneStartedFired`) ensure each event is fired only once per screen visit on the first edit.
- **Sliders (`onChangeEnd` vs `onChanged`):** Applied to `loan_amount_changed`. The capture call was placed in `Slider.onChangeEnd` instead of `Slider.onChanged`, ensuring only one event is sent per drag gesture when released, while `onChanged` is reserved strictly for updating the UI state.
- **Scrolls (`ScrollEndNotification`):** Applied to `offers_scrolled`. Instead of listening to continuous scroll updates, a `NotificationListener<ScrollEndNotification>` is used to record the final scroll offset once when scrolling stops.
- **Exact event names & properties preserved:** Applied across all events to ensure compatibility with existing dashboards and funnels.

### Which parts were ignored / did not apply:
- **Focus lost (`FocusNode` listener) for final field values:** Ignored/did not apply because neither the email nor the phone number should be captured as event properties (PII restriction in `docs/EVENTS.md`).
- **Tap/focus events via `FocusNode`:** Ignored because the specification specifically asks for typing started ("User started typing..."), which is naturally triggered on the first `onChanged` edit rather than just focusing/tapping the field without typing.
- **Debouncing:** Ignored in favor of the once-per-visit flag and `onChangeEnd` / `ScrollEndNotification` approaches, which cleaner match the event semantics.
