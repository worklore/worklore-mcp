# Analytics implementation

Implemented all six events in `docs/EVENTS.md` through the existing `Analytics.capture` wrapper.

- Registration sends `registration_email_started` and `registration_phone_started` once per screen visit, on the first edit. Neither event includes personal data.
- The slider sends `loan_amount_changed` with the chosen integer `amount` when a drag ends. The checkbox sends `terms_accepted` when ticked. Continue sends `registration_continue_tapped` with integer `amount` and boolean `terms` before opening offers.
- Offers sends `offers_scrolled` with a double `offset` when scrolling ends.

The colleague's note applied to text fields, the slider, and scrolling: capturing every keystroke or drag update would produce excessive events. I used once-per-visit flags for the text fields and gesture-end callbacks for the slider and list. Its PostHog debug-build and dashboard checks were not applicable to local verification; no external service was contacted.

Verification: `flutter analyze` completed with no issues.
