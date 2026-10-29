# Analytics events implemented

All six events from `docs/EVENTS.md` are in, using `Analytics.capture`, with exact names and properties. No PII is sent.

**Registration screen (`lib/screens/registration_screen.dart`)**
- `registration_email_started` / `registration_phone_started`: fire on the first `onChanged`, guarded by a per-screen-state flag. This is once per visit, not once per keystroke.
- `loan_amount_changed` (`amount`): fires from the slider's `onChangeEnd`, so once per drag. `onChanged` only updates the UI.
- `terms_accepted`: fires when the box is ticked. Unticking sends nothing.
- `registration_continue_tapped` (`amount`, `terms`): fires when Continue is tapped, just before navigating.

**Offers screen (`lib/screens/offer_screen.dart`)**
- `offers_scrolled` (`offset`): the screen is now a `StatefulWidget`. It listens for `ScrollEndNotification` and fires once per visit, with the scroll position when scrolling settles.

**Colleague's note: what applied**
- Applied: the per-keystroke, per-slider-step and per-scroll-update billing risk is real here, because the spec's "started typing", "moved the slider" and "scrolled" events would naturally be hooked to `onChanged` or scroll updates. I used once-per-visit flags for the text fields and the scroll, and `onChangeEnd` for the slider.
- Not applied: the focus-lost variant. No event needs a final field value. The `FocusNode` tap/focus variant wasn't needed either.
- Not applicable: the PostHog debug-log verification. I didn't run the app; there is no Flutter run here and I didn't use the SDK.

**Assumptions**
- Each of `terms_accepted` and `registration_continue_tapped` fires on every qualifying tap, which is bounded by user taps. Say if you want those capped too.
- `offers_scrolled` is once per screen visit, which matches the funnel step.
