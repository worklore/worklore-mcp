# Analytics implementation

Implemented all six events from `docs/EVENTS.md` through `Analytics.capture`:

- Registration: `registration_email_started` and `registration_phone_started` fire on the first edit of each field per screen visit. Neither field value is sent.
- `loan_amount_changed` fires when a slider interaction ends, with the chosen integer `amount`.
- `terms_accepted` fires when the checkbox is ticked.
- `registration_continue_tapped` fires before navigating to offers, with integer `amount` and boolean `terms`.
- Offers: `offers_scrolled` fires when the list stops scrolling, with the final double `offset`.

The colleague's note applies to the per-keystroke, per-slider-step, and per-scroll-update event volume risk. I used once-per-visit flags for text starts, `onChangeEnd` for the slider, and `ScrollEndNotification` for the list. Its focus-loss guidance does not apply because the spec does not request a final text value or a focus event. Screen views remain covered by the existing `PosthogObserver`.

Verification: `flutter analyze` completed with no issues. I did not run a PostHog debug session; the repository uses a placeholder project key.
