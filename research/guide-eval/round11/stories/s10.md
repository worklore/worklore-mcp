---
title: PostHog free tier gone in days? Flutter sent an event per keystroke
date: 2026-10-07
tags: [posthog, flutter, analytics, event-quota, pricing]
type: success
status: n/a
reproducible: true
visibility: public
stack: Flutter / Dart, posthog_flutter 5.x
agent: Claude Code
model: claude-opus-5-5
---

# PostHog free tier gone in days? Flutter sent an event per keystroke

Analytics tools like PostHog charge by the number of events. The free tier is
generous, so a small app should never run out. Ours used up the free monthly
event quota within a few days.

The cause was in our own code. Our product spec listed events like "user
started typing their email" and "user moved the loan amount slider". We hooked
them up in the obvious place: `onChanged`. In Flutter, a text field's
`onChanged` runs on every keystroke, and a slider's `onChanged` runs on every
step it crosses while the user drags. An email address became twenty events.
One drag across the slider became dozens. Multiply that by every field on
every registration screen, then by every user, and the quota was gone.

You can't see this in the PostHog dashboard. The event names were exactly
what the spec asked for and the funnels looked right. There were just far too
many of them.

The fix kept every event name and property the same. It only changed when
they fire:
- **Text fields:** fire once per screen visit, on the first edit. A
  `bool _emailInputFired` flag on the screen state does it. If you need the
  final value (only as a non-sensitive property, like "is valid"), fire when
  the field loses focus instead.
- **Sliders:** move the event from `onChanged` to `onChangeEnd`, so it fires
  once per drag, when the user lets go.
- **Scrolls:** the same idea. Listen for `ScrollEndNotification` rather than
  every scroll update.

## Check if this applies to you
Applies if: a Flutter app that sends events to PostHog (or any analytics
service billed per event).
Read-only steps:
1. `grep -rn "onChanged\|addListener\|NotificationListener<ScrollNotification>\|ScrollUpdateNotification" lib/`
2. For each hit, read the callback (and any method it calls) for
   `Posthog().capture`, your own capture wrapper, or an analytics `log` call.
Has the problem: a capture call runs inside an `onChanged`, a
`TextEditingController` / `ScrollController` listener, or a scroll-update
handler, without a once-only flag or debounce in front of it.
Doesn't have it: every capture inside those callbacks sits behind a
once-per-visit flag, or is in `onChangeEnd` / a focus-lost handler /
`ScrollEndNotification` instead.

## Reproduce this
Prerequisites: a Flutter app using
[posthog_flutter](https://pub.dev/packages/posthog_flutter) (or another
per-event-billed analytics SDK) with capture calls in widget callbacks.

Your agent will need from you: which of the events are allowed to stay
per-change (usually none); whether any event must carry the field's final
value.

Steps:
1. Run the check above and list every capture inside `onChanged`, a
   controller listener, or a scroll-update handler.
2. Text fields: add a `bool _<field>InputFired = false;` to the screen state.
   In `onChanged`, capture only `if (!_<field>InputFired)` and set the flag.
   If the state object survives navigation between steps, put the flag there
   and decide whether "once" means per visit or per flow.
3. Tap/focus events: capture in a `FocusNode` listener only when
   `hasFocus && !_tapFired`.
4. Events that need the final value: capture in the `FocusNode` listener when
   focus is lost (`!hasFocus`), not in `onChanged`.
5. Sliders: move the capture from `onChanged` to `onChangeEnd`. Keep
   `onChanged` for updating the UI only.
6. Scrolls: capture from `NotificationListener<ScrollEndNotification>`,
   never from `ScrollUpdateNotification` or a `ScrollController` listener.
7. Keep event names and properties unchanged, so existing dashboards and
   funnels keep working.

Verify: run a debug build with `PostHogConfig.debug = true`. Type a 20-letter
value into a fixed field: the log shows one `*_input` capture, not twenty.
Drag a slider end to end: one event when you let go. In PostHog → Activity,
the event count per session for these events drops to 1.
