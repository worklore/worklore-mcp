# Change

`gen.py` `hr_target()`: the lower bound key is now `start` instead of `value`
(`{"units": "%lthr", "start": lo, "end": hi}`).

# Why

The readback (`readback/event-184233-as-sent.json`) shows we sent
`{value, end}`. Per the colleague's finding, `value`+`end` is exported to FIT as
a zone-mapped Lap-HR target, so the watch snaps it to its own zone bands. That
matches `readback/watch-notes.md` exactly (118–137, 151–162, 137–151 ...,
always zone edges, even after changing the watch LTHR). `start`+`end` exports
as an Instant-HR corridor showing the raw bpm Intervals computes from its
LTHR (172).

# Colleague's note: what applied
- Applied: `start` vs `value` rename; keep `%lthr` percentages (already the case;
  `bpm` and `start_bpm`/`end_bpm` were already ruled out in our notes).
- Not applied: the top-level `description` text grammar (UI step chart). It is
  not part of the watch symptom, and I can't test the Intervals parser here
  (a bad description wipes the steps), so I left it out.

# Not verified
No access to Intervals or the watch. Check by pushing a new event, reading it
back (steps non-empty, `start` present) and confirming the watch shows
e.g. Float 129–141 bpm. Existing event 184233 was sent with the old shape and
needs re-pushing.
