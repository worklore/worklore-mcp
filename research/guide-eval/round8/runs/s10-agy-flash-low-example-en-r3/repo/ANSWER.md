# Implementation of Product Analytics Events

Implemented the events defined in `docs/EVENTS.md` across `RegistrationScreen` (`lib/screens/registration_screen.dart`) and `OfferScreen` (`lib/screens/offer_screen.dart`) using `Analytics.capture`.

## Implemented Events

1. **`registration_email_started`**
   - **Location:** `lib/screens/registration_screen.dart` in email `TextField.onChanged`.
   - **Behavior:** Fires once per screen visit on the first keystroke using a `_emailStartedFired` boolean guard. No PII is sent.
2. **`registration_phone_started`**
   - **Location:** `lib/screens/registration_screen.dart` in phone `TextField.onChanged`.
   - **Behavior:** Fires once per screen visit on the first keystroke using a `_phoneStartedFired` boolean guard. No PII is sent.
3. **`loan_amount_changed`**
   - **Location:** `lib/screens/registration_screen.dart` on `Slider.onChangeEnd`.
   - **Properties:** `{'amount': v.round()}` (int).
   - **Behavior:** Fires only when the user finishes dragging the slider, avoiding firing on every intermediate drag step.
4. **`terms_accepted`**
   - **Location:** `lib/screens/registration_screen.dart` in `CheckboxListTile.onChanged`.
   - **Properties:** None.
   - **Behavior:** Fires only when the user ticks the checkbox (`newValue && !_terms`).
5. **`registration_continue_tapped`**
   - **Location:** `lib/screens/registration_screen.dart` in `FilledButton.onPressed`.
   - **Properties:** `{'amount': _amount.round(), 'terms': _terms}` (`amount` int, `terms` bool).
   - **Behavior:** Fires when the enabled Continue button is pressed right before navigation.
6. **`offers_scrolled`**
   - **Location:** `lib/screens/offer_screen.dart` in `NotificationListener<ScrollEndNotification>`.
   - **Properties:** `{'offset': notification.metrics.pixels}` (double).
   - **Behavior:** Fires when scrolling completes (`ScrollEndNotification`) rather than on every pixel scroll update.

---

## Colleague's Note: What Applied and What Was Ignored

### Parts that applied:
- **Text fields (once-per-visit flag):** Applied the recommendation to use a boolean flag (`_emailStartedFired` and `_phoneStartedFired`) in the screen state to ensure `registration_email_started` and `registration_phone_started` fire only once on the first edit instead of on every keystroke.
- **Sliders (`onChangeEnd`):** Applied moving the analytics event tracking to `Slider.onChangeEnd` instead of `onChanged`. UI updates stay responsive in `onChanged`, while the `loan_amount_changed` event fires once per drag with the final chosen integer amount.
- **Scrolls (`ScrollEndNotification`):** Applied wrapping `ListView.builder` with `NotificationListener<ScrollEndNotification>` to capture `offers_scrolled` only upon scroll completion rather than on every scroll tick.
- **Event names and properties:** Kept all event names and property schemas exact to spec.

### Parts ignored / not applicable:
- **Focus lost (`FocusNode` listener for final value):** Not applicable, because the spec did not ask for the final text input values (in fact, `docs/EVENTS.md` explicitly forbids sending email and phone number due to PII).
- **PostHog debug verification steps (`PostHogConfig.debug = true` / PostHog dashboard checks):** Not applicable in this test/offline environment without a live backend or mobile simulator session.
