# round 8 follow-up: does a freshness cue bring Codex back to the web under a Russian task?

Question from a Reddit reader (2026-10-30): the Russian task dropped Codex's web search to zero on the
Garmin story (s1). Does naming something clearly newer than the model's training data flip it back?

One sentence added to the s1 task, in both languages, nothing else changed (same fixture, same suffix):

- en: "Intervals.icu updated its workout export format in October 2026."
- ru: "Intervals.icu обновил формат экспорта тренировок в октябре 2026."

Arms: fresh-en, fresh-ru. Agents: codex-sol (medium), codex-sol-low. 5 repetitions. No story.
Baseline is round 8's none-en / none-ru for the same cells.

## Result (2026-10-30, 20 runs)

| Setup | Arm | searched | passed | round 8 baseline (no cue) |
|---|---|---|---|---|
| Codex medium | Russian + cue | 0/5 | 0/5 | searched 0/5, passed 0/5 |
| Codex low | Russian + cue | 0/5 | 0/5 | searched 0/5, passed 0/5 |
| Codex medium | English + cue | 5/5 | 4/5 | searched 3/5, passed 3/5 |
| Codex low | English + cue | 5/5 | 3/5 | searched 5/5, passed 5/5 |

The cue re-armed nothing in Russian: not one of the ten runs opened the web, and every
command in their logs is cat, ls, git or python3 on local files. In English the same
sentence made every run search, and the queries quote it back ("site:forum.intervals.icu
October 2026 Garmin workout HR range"). So the freshness cue is read and acted on in
English and ignored in Russian; whatever stops the search under a Russian task sits
before the cue, not after it. The three English failures with the cue (against two of ten
without it) are runs the sentence misled: they searched for the "October 2026 change",
found forum threads about workout text, and moved the generator from `workout_doc` to
workout text in the description, citing the forum. A freshness cue that is not true
costs accuracy in the language where it is read.
