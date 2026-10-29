# Implementation of Analytics Events

## Overview of Changes

Implemented the product analytics events specified in `docs/EVENTS.md` across `RegistrationScreen` (`lib/screens/registration_screen.dart`) and `OfferScreen` (`lib/screens/offer_screen.dart`), routing all calls through the existing `Analytics.capture` wrapper (`lib/analytics.dart`).

### Implemented Events & Behavior

1. **`registration_email_started`**
   - Triggered when the user starts typing their email into the email `TextField`.
   - Fires once per screen visit using a `_emailStartedFired` boolean guard.
   - Does not send email address or PII.

2. **`registration_phone_started`**
   - Triggered when the user starts typing their phone number into the phone `TextField`.
   - Fires once per screen visit using a `_phoneStartedFired` boolean guard.
   - Does not send phone number or PII.

3. **`loan_amount_changed`**
   - Triggered on the loan amount `Slider` using `onChangeEnd` rather than `onChanged`.
   - Fires once per drag gesture when the user releases the slider.
   - Payload: `{'amount': v.round()}` (integer).

4. **`terms_accepted`**
   - Triggered on the terms and conditions `CheckboxListTile` when `onChanged` transitions the checkbox to `true`.
   - No properties sent.

5. **`registration_continue_tapped`**
   - Triggered when the user taps the enabled "Continue" `FilledButton`.
   - Payload: `{'amount': _amount.round(), 'terms': _terms}`.

6. **`offers_scrolled`**
   - Triggered on the offers list in `OfferScreen` using `NotificationListener<ScrollEndNotification>` wrapping the `ListView.builder`.
   - Fires when the scroll gesture ends instead of on every scroll pixel update.
   - Payload: `{'offset': notification.metrics.pixels}` (`double`).

---

## Colleague's Note: What Applied and What Was Ignored

### Parts that Applied:
- **Text fields once-per-visit flag:** Added `bool _emailStartedFired` and `bool _phoneStartedFired` to `_RegistrationScreenState` and checked `if (!_emailStartedFired)` / `if (!_phoneStartedFired)` before firing the `*_started` events inside `onChanged`. This avoids capturing an event on every keystroke and protects the event quota.
- **Slider `onChangeEnd` instead of `onChanged`:** Moved `loan_amount_changed` capture into the `Slider`'s `onChangeEnd` callback so it captures once per drag release instead of emitting events on every step crossed during a drag, while keeping `onChanged` for live UI updates.
- **Scrolls with `ScrollEndNotification`:** Used `NotificationListener<ScrollEndNotification>` to listen for when scrolling ends rather than capturing on `ScrollUpdateNotification` or raw scroll controller updates, sending the final `metrics.pixels` as `offset`.
- **Preserved event names and property schemas:** Kept all event names and property keys exactly as required by the specification.

### Parts that Were Ignored:
- **FocusNode listeners for focus loss / tap:** The spec explicitly defined "user started typing" rather than field focus/tap or field blur/validation, so simple first-input guards inside `onChanged` were sufficient without attaching `FocusNode`s.
- **Debouncing:** Once-per-visit flags and `onChangeEnd`/`ScrollEndNotification` directly satisfied the event firing semantics without needing debounce timers.
- **Debug verification (`PostHogConfig.debug = true` / PostHog UI checks):** Not applicable in this headless offline test environment.
