# Implementation of Analytics Events

## Overview of Changes

Implemented all product analytics events defined in `docs/EVENTS.md` across `lib/screens/registration_screen.dart` and `lib/screens/offer_screen.dart` using `Analytics.capture`.

### Events Implemented

1. **`registration_email_started`** (`lib/screens/registration_screen.dart`):
   - Fired once when the user begins typing into the email `TextField` (guarded by `_emailStartedFired` flag and checking `text.isNotEmpty`).
   - No PII is sent as properties.

2. **`registration_phone_started`** (`lib/screens/registration_screen.dart`):
   - Fired once when the user begins typing into the phone `TextField` (guarded by `_phoneStartedFired` flag and checking `text.isNotEmpty`).
   - No PII is sent as properties.

3. **`loan_amount_changed`** (`lib/screens/registration_screen.dart`):
   - Hooked up to `Slider.onChangeEnd` instead of `onChanged` so that the event fires only once per drag gesture when the user releases the slider thumb.
   - Sent property: `{'amount': v.round()}` (int).

4. **`terms_accepted`** (`lib/screens/registration_screen.dart`):
   - Fired in `CheckboxListTile.onChanged` when the checkbox transition is to `checked` (`true`).
   - No properties sent.

5. **`registration_continue_tapped`** (`lib/screens/registration_screen.dart`):
   - Fired in the Continue `FilledButton.onPressed` handler before navigating to `/offers`.
   - Sent properties: `{'amount': _amount.round(), 'terms': _terms}` (`amount` as int, `terms` as bool).

6. **`offers_scrolled`** (`lib/screens/offer_screen.dart`):
   - Wrapped `ListView.builder` in a `NotificationListener<ScrollEndNotification>` to capture scroll events only once when scrolling finishes (resting offset), rather than on every scroll tick.
   - Sent property: `{'offset': notification.metrics.pixels}` (double).

---

## Colleague's Note: What Applied and What Was Ignored

The colleague's note highlighted quota exhaustion on event-billed analytics (like PostHog) caused by capturing events inside high-frequency callbacks (`onChanged`, slider dragging, continuous scroll notifications).

### What Applied:
- **Text fields (once-per-visit flag):** Used boolean flags (`_emailStartedFired`, `_phoneStartedFired`) on `_RegistrationScreenState` so that `registration_email_started` and `registration_phone_started` fire only once when typing begins, rather than per keystroke in `onChanged`.
- **Sliders (`onChangeEnd`):** Used `onChangeEnd` on the loan amount `Slider` to fire `loan_amount_changed` once per drag gesture completion rather than every intermediate step during drag.
- **Scrolls (`ScrollEndNotification`):** Wrapped the list in `NotificationListener<ScrollEndNotification>` so `offers_scrolled` fires only when the user finishes scrolling rather than on every frame / `ScrollUpdateNotification`.
- **Preserved event contracts:** Event names and property names/types strictly match the spec in `docs/EVENTS.md`.

### What Was Ignored / Did Not Apply:
- **`FocusNode` listeners for tap/focus or focus lost:** The spec required detecting when the user started typing (`registration_email_started`, `registration_phone_started`) rather than focus/tap, and does not require capturing final values on blur. Therefore, focus-loss listeners were not needed.
- **Debouncing:** Once-per-visit guards and `onChangeEnd`/`ScrollEndNotification` native callbacks completely solved event throttling without needing timer-based debounce logic.
- **State survival across flow navigation:** The registration screen is a single step that navigates forward to offers via standard route push, so local state variables on `_RegistrationScreenState` are properly scoped per visit.
