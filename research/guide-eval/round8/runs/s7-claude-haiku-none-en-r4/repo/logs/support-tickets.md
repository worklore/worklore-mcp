# Support tickets — Intervals.icu connection

## #214 — "Connect Intervals.icu shows Unauthorized" (C. Okafor, 2026-10-14)

> I'm signed in, the page says "Signed in as C. Okafor", I click Connect
> Intervals.icu and get a white page that just says
> `{"error": "unauthorized"}`. Back button, try again, same thing. Tried
> Safari and Chrome.

Reproduced with my own account. Same for the four athletes onboarded this
week; every athlete who clicks Connect ends up on that page. Nobody has
gotten through the button since we started onboarding athletes.

## #219 — "Says I need to reconnect" (T. Rivera, 2026-10-16)

> My Intervals was connected during the onboarding call last month and
> wellness showed up fine that evening. Next morning the card said
> "Status: expired, reconnect". I clicked Connect and got the same
> unauthorized page as Chloe. I did NOT revoke anything on the Intervals
> side — tricoach is still listed under my Intervals apps.

Checked our logs for the onboarding day: Rivera's connection was marked
"expired, reconnect" about an hour after it was made (see
`connect-attempt.log`). Rivera was connected by me pasting the authorize
link into their browser during the call, which is how I got around the
button. Pasting the link does not work anymore either: since the calendar
sync shipped on 2026-10-02 the integration also asks for calendar access, and
Intervals now answers the authorize step with an error page before the
athlete ever sees the consent screen (captured below in
`connect-attempt.log`).
