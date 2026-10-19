# HR corridors clamped to watch zones — fix

## What changed

`gen.py`, `hr_target()`: the lower bound of the HR target is now emitted as
`start` instead of `value`:

```diff
-    return {"units": "%lthr", "value": lo, "end": hi}
+    return {"units": "%lthr", "start": lo, "end": hi}
```

(plus a docstring explaining why, so nobody "tidies" it back to `value`).
The percentages, the `%lthr` units, and everything else in the event body are
unchanged.

## Why

`readback/watch-notes.md` shows every step landing exactly on one of the
watch's zone bands (118–137, 151–162, 137–151), and changing the watch's LTHR
moves the bands but never produces the planned 151–160 / 129–141. That's the
signature of a zone-mapped target: Intervals exports `{value, end}` as a
"Lap HR" / zone-based target in the FIT file, and the watch snaps it to its
own zones. The `{start, end}` shape is what Intervals uses for an exact
("Instant HR") corridor; it exports the bpm range Intervals computes from its
own LTHR (172), so the watch shows that range regardless of its own
auto-detected LTHR (168).

Expected on the watch after re-pushing `plans/tempo-run.json`:
warm-up 117–129, tempo 151–160, float 129–141, cool-down 112–124 bpm.

## Not verified

I did not push anything or touch Intervals/Garmin (ground rules). I checked
only that `gen.py` now outputs `start`/`end` for every HR step and no `value`
key. To confirm: regenerate, push, `GET` the event to check `start` survives
the round-trip and `workout_doc.steps` is non-empty, sync the watch, and
compare the corridors against the table above. The watch's LTHR (168) differs
from Intervals' (172), so you'll be able to tell which one was used.

## Which parts of the colleague's note applied

- **Applied:** the main point, `start`/`end` instead of `value`/`end`. It
  matches our symptoms exactly, including the same two failed attempts we had
  already made (`units: "bpm"` → 214–249, `start_bpm`/`end_bpm` → constant
  101). I also kept their advice to send percentages of LTHR (`%lthr`), not
  absolute bpm. The generator was already doing that.
- **Applied as a verification step only:** read the event back via the API
  and sync to the watch to confirm (see above).
- **Not applied:** the "bonus trap" about a top-level `description` in
  Intervals' text grammar (`m` = minutes, `mtr`/`km`, bare `Z2` = power,
  leading digits in labels). Our readback shows `workout_doc.steps` populated
  and there's no report of steps missing from the web UI. `gen.py` doesn't
  send a `description` at all, so that parser can't wipe anything. Adding one
  would be a separate change with its own risks, so I left it out. If the
  steps ever turn out to be invisible in the Intervals web UI, that note is
  where to look.
- **Not relevant:** the dropdown/units-label digression and the OAuth/account
  prerequisites.
