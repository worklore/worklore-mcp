# Analytics implementation

Implemented all six events in `docs/EVENTS.md` using the existing `Analytics.capture` wrapper.

- Registration captures the first email and phone edit once per screen visit, with no personal data; the chosen loan amount when a slider interaction ends; each transition to accepted terms; and each enabled Continue tap with `amount` and `terms` properties.
- Offers captures `offers_scrolled` when vertical scrolling ends at a positive offset, with the pixel offset as a double.
- Event names and properties match the spec. Existing automatic screen view tracking remains in place.

The colleague's note applies to the email and phone `onChanged` callbacks, the slider, and offers scrolling: capturing every edit or scroll update could produce many billable events. The implementation uses once-per-visit flags, `onChangeEnd`, and `ScrollEndNotification` respectively. Its focus-node advice does not apply because the spec asks for typing starts, not focus or final field values. The note's PostHog debug and dashboard checks were not run; they require a running app and configured PostHog project.

Verification: `flutter analyze` reported no issues, and `git diff --check` passed.
