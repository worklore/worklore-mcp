# Analytics Events Implementation

## 1. Events Implemented

All product events specified in `docs/EVENTS.md` were implemented using the existing `Analytics` wrapper (`Analytics.capture`):

1. **`registration_email_started`** (`lib/screens/registration_screen.dart`):
   - Fired when the user starts typing their email in the email text field.
   - Guarded by a state boolean flag `_emailStartedFired` so it only fires once on the first keystroke per screen visit (no PII transmitted).

2. **`registration_phone_started`** (`lib/screens/registration_screen.dart`):
   - Fired when the user starts typing their phone number in the phone text field.
   - Guarded by a state boolean flag `_phoneStartedFired` so it only fires once on the first keystroke per screen visit (no PII transmitted).

3. **`loan_amount_changed`** (`lib/screens/registration_screen.dart`):
   - Fired when the user moves the loan amount slider and releases it (`onChangeEnd`).
   - Captures property `{'amount': v.round()}` (int).

4. **`terms_accepted`** (`lib/screens/registration_screen.dart`):
   - Fired when the user ticks the terms and conditions checkbox (`onChanged` when `v == true`).
   - Carries no properties.

5. **`registration_continue_tapped`** (`lib/screens/registration_screen.dart`):
   - Fired when the user taps Continue when the button is enabled.
   - Captures properties `{'amount': _amount.round(), 'terms': _terms}` (`amount` as int, `terms` as bool).

6. **`offers_scrolled`** (`lib/screens/offer_screen.dart`):
   - Fired when the user finishes scrolling the offers list via `NotificationListener<ScrollEndNotification>`.
   - Captures property `{'offset': notification.metrics.pixels}` (`offset` as double).

---

## 2. Colleague's Note: What Applied and What Did Not

### Parts that applied:
- **Text fields (keystroke explosion fix):** 
  - *Applied:* Used `bool _emailStartedFired = false;` and `bool _phoneStartedFired = false;` on the screen state. In `onChanged`, the events `registration_email_started` and `registration_phone_started` fire only on the first keystroke (`if (!_emailStartedFired)`), avoiding an event per keystroke while preserving privacy (no PII logged).
- **Sliders (drag explosion fix):** 
  - *Applied:* Placed `loan_amount_changed` in `onChangeEnd` instead of `onChanged`. UI state updates continuously via `onChanged`, but the analytics event fires only once per drag when the user finishes dragging.
- **Scrolls (scroll update explosion fix):** 
  - *Applied:* Wrapped the `ListView.builder` with `NotificationListener<ScrollEndNotification>` to capture `offers_scrolled` with `offset: notification.metrics.pixels`, preventing capture spam on every scroll pixel/update.
- **Event names and properties integrity:** 
  - *Applied:* Maintained exact snake_case event names and data types (`amount` as int, `terms` as bool, `offset` as double).

### Parts that did not apply / were ignored:
- **FocusNode listeners for focus loss / tap events:**
  - *Ignored:* The product specification for text fields only requested "started typing" events, not focus-change or final-value-on-blur events.
- **Debounce mechanisms:**
  - *Ignored:* Once-per-visit flags and Flutter's built-in `onChangeEnd` / `ScrollEndNotification` listeners were simpler, idiomatic, and sufficient without needing debounce timers.
- **Debugging configuration (`PostHogConfig.debug = true`) and checking PostHog dashboard:**
  - *Ignored:* External network services and publishing/reporting are disallowed, and `PostHogConfig` in this environment does not expose or require changing the global debug configuration in code.
