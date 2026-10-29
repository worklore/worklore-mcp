# HR corridors clamped to watch zones — fix

## What changed

`gen.py`, `hr_target()`: the HR target's lower bound is now emitted as
`start` instead of `value`:

```diff
-    return {"units": "%lthr", "value": lo, "end": hi}
+    return {"units": "%lthr", "start": lo, "end": hi}
```

I also added a docstring note explaining why the key name matters. Nothing
else changed. `python3 gen.py plans/tempo-run.json` now emits
`{"units": "%lthr", "start": …, "end": …}` for all four HR steps, and no
`value` keys at all.

## Why

`readback/watch-notes.md` shows every planned corridor replaced by one of the
watch's own zone bands (e.g. Float 75–82% → 137–151, which is the watch's Z3).
Changing the watch's LTHR moved the bands, but the targets still sat on zone
edges. So the targets are reaching the watch as *zone* targets, not as bpm
ranges. The API readback (`event-184233-as-sent.json`) shows the API accepted
`{value, end}` as sent. That means the problem is in how Intervals exports
the target to FIT, not in API validation.

When Intervals exports a `{value, end}` HR target to FIT, it sends it as a
zone-mapped target, and the watch snaps that to its local zones. A
`{start, end}` target is exported as an instant-HR corridor in the bpm that
Intervals computed from its own LTHR (172). With this change the watch should
show the planned ranges: 117–129, 151–160, 129–141, 112–124.

Units stay `%lthr`. The earlier `units: "bpm"` attempt (214–249) and the
`start_bpm`/`end_bpm` attempt (constant 101) were both dead ends, and the
notes record both, so this fix doesn't go back to either.

## Not verified yet

I haven't pushed anything or synced a watch, per the ground rules. To confirm:
regenerate, `./push.sh event.json`, run `GET` on the event and check that
`workout_doc.steps` is populated with `start`/`end` targets, then sync and
check the Float step. It should read 129–141, not 137–151. The current
difference between the two LTHRs (172 in Intervals, 168 on the watch) makes
this easy to see.

## Which parts of the colleague's note applied

- **Applied:** the main finding, that `start` rather than `value` on the
  lower bound switches the FIT export from a zone-mapped target to an
  instant-HR corridor. Our symptoms match theirs exactly: the same failed
  attempts (`bpm` → 214–249, `start_bpm`/`end_bpm` → 101) and the same
  LTHR numbers. I also kept their advice to use `%lthr` percentages rather
  than absolute bpm, which this generator already did.
- **Applied as a verification method:** their check of
  readback → sync → compare against Intervals' LTHR rather than the watch's,
  described above. I couldn't run it here.
- **Not applied:** the "bonus trap" about the top-level `description` text
  grammar (`m` = minutes, `mtr`/`km`, bare `Z2` meaning power, blank lines
  around repeats). Our notes report no problem with steps showing in the web
  UI, and `workout_doc.steps` came back populated. Adding a `description`
  could make things worse: if Intervals' parser rejects it, Intervals wipes
  both representations. If steps ever fail to show in the Intervals UI, come
  back to that section.
- **Not applied:** the account, credential and Garmin prerequisites and the
  test-event steps. Those are for running the end-to-end check, which is
  outside what I'm allowed to do here.
