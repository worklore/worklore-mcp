#!/usr/bin/env bash
# Writes tickets/<s>.md (the same facts as the story, as a plain ticket comment, without the reproduction contract)
# from stories/<s>.md with Codex (GPT-6-Sol, read-only), one call per story.
# Codex, not Claude, writes them: the stories were drafted with Claude, so a different author keeps the ticket wording
# from echoing the story's. Every ticket is then checked by hand against what its grader needs (tickets/CHECK.md).
D="$(cd "$(dirname "$0")/.." && pwd)"
S=("$@"); [ ${#S[@]} -eq 0 ] && S=(s1 s3 s7 s8 s10 s11)
for s in "${S[@]}"; do
  P="Rewrite the developer note below as the comment a colleague leaves on an internal bug ticket after fixing a similar case.

A ticket comment says what happened: the symptom, what was tried and how each attempt failed, the cause, the fix, and any traps found on the way. Keep every one of those facts: every file name, setting, key, value, error text and detail of the fix. Code, commands and config lines that show the cause or the fix may stay, inline or as short code blocks.

Leave out the note's reproduction contract, the part that tells another person how to redo the work: prerequisites, what the agent needs from the user, step-by-step instructions, Verify criteria, and any 'Check if this applies' section. A fact that appears only in that part and is not an instruction (a cause, a value, a trap) still goes into the comment, said as something you found.

No title, no frontmatter, no headings, no numbered or bulleted lists. Plain paragraphs in the first person, past tense, the way people write ticket comments. Do not add any fact, advice or code that the note does not contain. Output only the comment text.

--- the note ---
$(cat "$D/stories/$s.md")"
  (cd "$(mktemp -d)" && codex exec --skip-git-repo-check -s read-only -o "$D/tickets/$s.md" "$P" < /dev/null > /dev/null 2>&1) &
done
wait
