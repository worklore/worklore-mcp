# Analytics implementation

Added all six events from `docs/EVENTS.md` through the existing `Analytics.capture` wrapper.

- Registration sends email and phone start events once per screen instance, without either value as a property.
- The loan amount event sends the selected integer amount when a slider interaction ends.
- Terms acceptance fires when the checkbox changes to checked. Continue sends the current integer amount and terms state when tapped.
- Offers sends the scroll offset as a double when scrolling ends beyond the top of the list.

The colleague's note applied to the text fields, slider, and scrolling: their high-frequency callbacks would otherwise create excessive events. I used once-only flags for typing and end-of-interaction callbacks for the slider and list. Its PostHog debug-mode and dashboard verification steps were not applicable to local static verification; no events were sent to an external service.

Verification: `flutter analyze` completed with no issues. `git diff --check` passed.
