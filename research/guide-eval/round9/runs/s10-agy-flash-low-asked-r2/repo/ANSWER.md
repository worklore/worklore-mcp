# Analytics Implementation

## Worklore Stories
Before starting, we queried the `worklore` MCP server for stories relevant to this project (`suggest_for_project`).
It returned the story:
- **`2026-10-07-posthog-free-tier-gone-in-days-flutter-sent-an-event-per-key`**: *PostHog free tier gone in days? Flutter sent an event per keystroke*.

Following its guidance:
- For text fields (`registration_email_started`, `registration_phone_started`), we fired the event only once upon the first user input rather than on every keystroke in `onChanged`.
- For the loan amount slider (`loan_amount_changed`), we hooked the event into `onChangeEnd` instead of `onChanged` so that an event is only dispatched when the user finishes dragging the slider, preventing event flooding.
- For scrolling (`offers_scrolled`), we used `NotificationListener<ScrollEndNotification>` around the `ListView` so that scrolling emits an event when scrolling ends rather than flooding updates per pixel frame.

## Implemented Events
Implemented all product funnel events specified in `docs/EVENTS.md` using `Analytics.capture(...)`:

1. **`registration_email_started`** (`lib/screens/registration_screen.dart`):
   - Fired once when the user begins typing their email address in the Email `TextField`.
   - No PII is passed.

2. **`registration_phone_started`** (`lib/screens/registration_screen.dart`):
   - Fired once when the user begins typing their phone number in the Phone `TextField`.
   - No PII is passed.

3. **`loan_amount_changed`** (`lib/screens/registration_screen.dart`):
   - Fired in `onChangeEnd` on the `Slider` when the user finishes dragging.
   - Property: `amount` (int, `_amount.round()`).

4. **`terms_accepted`** (`lib/screens/registration_screen.dart`):
   - Fired in `CheckboxListTile.onChanged` when the user ticks the terms and conditions checkbox (`accepted == true`).

5. **`registration_continue_tapped`** (`lib/screens/registration_screen.dart`):
   - Fired when the user taps the Continue `FilledButton`.
   - Properties: `amount` (int), `terms` (bool).

6. **`offers_scrolled`** (`lib/screens/offer_screen.dart`):
   - Fired when scrolling ends via `NotificationListener<ScrollEndNotification>` wrapping the `ListView.builder`.
   - Property: `offset` (double, `notification.metrics.pixels`).
