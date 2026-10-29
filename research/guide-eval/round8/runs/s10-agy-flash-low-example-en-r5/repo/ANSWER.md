# Implementation Summary: Analytics Events

## Overview of Changes

Implemented product analytics events defined in `docs/EVENTS.md` across `lib/screens/registration_screen.dart` and `lib/screens/offer_screen.dart` using `Analytics.capture`.

### 1. `lib/screens/registration_screen.dart`
- **`registration_email_started`**: Tracked when the user starts typing their email. Fired once per screen visit on the first edit using a boolean flag `_emailStartedFired`. No PII (email content) is sent.
- **`registration_phone_started`**: Tracked when the user starts typing their phone number. Fired once per screen visit on the first edit using a boolean flag `_phoneStartedFired`. No PII (phone number content) is sent.
- **`loan_amount_changed`**: Tracked when the user changes the loan amount slider. Fired via `Slider.onChangeEnd` when the user releases the slider, passing `{'amount': v.round()}` (`int`).
- **`terms_accepted`**: Tracked when the terms and conditions checkbox is ticked (`accepted == true`).
- **`registration_continue_tapped`**: Tracked when the user taps the Continue button, passing `{'amount': _amount.round(), 'terms': _terms}` (`amount` as `int`, `terms` as `bool`).

### 2. `lib/screens/offer_screen.dart`
- **`offers_scrolled`**: Tracked when the user scrolls the offers list by wrapping `ListView.builder` in a `NotificationListener<ScrollEndNotification>`. Captures `{'offset': notification.metrics.pixels}` (`double`) on scroll end.

---

## Colleague Note Application

From the colleague's note on PostHog event quota exhaustion:

### Parts that applied:
- **Text fields (keystroke storm prevention):** Fired `registration_email_started` and `registration_phone_started` once per screen visit on the first edit using boolean flags (`_emailStartedFired` and `_phoneStartedFired`), rather than emitting events on every keystroke in `onChanged`.
- **Sliders:** Moved `loan_amount_changed` to `Slider.onChangeEnd` instead of `onChanged` so an event fires once per drag upon release rather than for every intermediate step.
- **Scrolls:** Used `NotificationListener<ScrollEndNotification>` to capture `offers_scrolled` at the completion of a scroll gesture rather than listening to continuous scroll updates or intermediate notifications.
- **Exact Event Names & Properties:** Kept event names and parameter types (`int`, `bool`, `double`) strictly aligned with `docs/EVENTS.md`.

### Parts that did not apply:
- **FocusNode listeners for focus loss:** Not needed here because the text field events (`registration_email_started`, `registration_phone_started`) only indicate when typing started and do not require emitting final field values.
- **Debounce or scroll controllers:** `ScrollEndNotification` handled scroll tracking cleanly without needing custom controllers or timers.
- **Debug flag verification (`PostHogConfig.debug`):** The app does not configure live keys or connect to network services in test/CI environments.
