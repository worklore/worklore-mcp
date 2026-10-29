# Implementation Summary: Analytics Events

## Overview
Implemented the product analytics events defined in `docs/EVENTS.md` across `RegistrationScreen` (`lib/screens/registration_screen.dart`) and `OfferScreen` (`lib/screens/offer_screen.dart`), using the existing `Analytics.capture` wrapper (`lib/analytics.dart`).

## Events Implemented

1. **`registration_email_started`**
   - **Location:** `lib/screens/registration_screen.dart` in `TextField` (`_email`) `onChanged`.
   - **Trigger:** Fired once per screen visit on the first keystroke in the email input field using a `_emailStartedFired` boolean guard.
   - **Properties:** None (no PII sent).

2. **`registration_phone_started`**
   - **Location:** `lib/screens/registration_screen.dart` in `TextField` (`_phone`) `onChanged`.
   - **Trigger:** Fired once per screen visit on the first keystroke in the phone input field using a `_phoneStartedFired` boolean guard.
   - **Properties:** None (no PII sent).

3. **`loan_amount_changed`**
   - **Location:** `lib/screens/registration_screen.dart` in `Slider` `onChangeEnd`.
   - **Trigger:** Fired when the user finishes dragging/adjusting the loan amount slider (upon release), preventing per-step event floods during dragging.
   - **Properties:** `{'amount': v.round()}` (`amount` as `int`).

4. **`terms_accepted`**
   - **Location:** `lib/screens/registration_screen.dart` in `CheckboxListTile` `onChanged`.
   - **Trigger:** Fired when the user checks/ticks the terms checkbox (`accepted && !_terms`).
   - **Properties:** None.

5. **`registration_continue_tapped`**
   - **Location:** `lib/screens/registration_screen.dart` in `FilledButton` `onPressed`.
   - **Trigger:** Fired when the user taps Continue when the form is valid.
   - **Properties:** `{'amount': _amount.round(), 'terms': _terms}` (`amount` as `int`, `terms` as `bool`).

6. **`offers_scrolled`**
   - **Location:** `lib/screens/offer_screen.dart` wrapping `ListView.builder` in a `NotificationListener<ScrollEndNotification>`.
   - **Trigger:** Fired only when scrolling ends, avoiding high-frequency events on every scroll position change/frame.
   - **Properties:** `{'offset': notification.metrics.pixels}` (`offset` as `double`).

---

## Colleague's Note: What Applied and What Was Ignored

### Parts that applied:
- **Text fields once-per-visit flag:** As recommended in the note ("Text fields: add a `bool _<field>InputFired = false;` to the screen state. In `onChanged`, capture only `if (!_<field>InputFired)` and set the flag"), flags (`_emailStartedFired` and `_phoneStartedFired`) were added to `_RegistrationScreenState` so `registration_email_started` and `registration_phone_started` fire only on the initial keystroke rather than on every keystroke.
- **Slider drag completion (`onChangeEnd`):** Following the recommendation to move slider captures from `onChanged` to `onChangeEnd`, `loan_amount_changed` is sent in `onChangeEnd` with the final rounded integer value, keeping `onChanged` exclusively for updating the UI state while dragging.
- **Scroll notifications (`ScrollEndNotification`):** Following the recommendation to listen for `ScrollEndNotification` rather than scroll updates, `ListView.builder` in `OfferScreen` is wrapped with `NotificationListener<ScrollEndNotification>` to capture `offers_scrolled` with `offset: notification.metrics.pixels` only when scrolling comes to a stop.
- **Preserving event names and properties:** All event names and payload keys/types match the exact specification in `docs/EVENTS.md`.

### Parts that were ignored / did not apply:
- **FocusNode listeners for field exit/focus loss:** Not needed because `registration_email_started` and `registration_phone_started` only track when typing started (no field value properties or validation properties required).
- **Tap/focus events on focus gain (`hasFocus && !_tapFired`):** The spec explicitly defined "User started typing their email/phone", not when focusing the field without typing.
- **ScrollController listeners / ScrollUpdateNotification cleanup:** There was no existing `ScrollController` listener or `ScrollUpdateNotification` in `OfferScreen` to refactor; `ScrollEndNotification` was directly introduced.
- **Debugging/PostHog dashboard verification instructions:** Instructions regarding checking PostHog dashboard or remote session activity were not applicable given the requirement to work strictly locally without external network/service interaction.
