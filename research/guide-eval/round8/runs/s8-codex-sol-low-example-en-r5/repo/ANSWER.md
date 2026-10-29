# Prompt cache fix

Changed `build_system()` in `bot.py` to send two text blocks, each with an ephemeral cache marker. The first contains only the byte-stable coaching instructions. The second contains the date and athlete context, including long-term facts. The assembled prompt text and tool selection are unchanged.

After `save_fact`, the context block changes, but the instruction block remains the same cached prefix. This addresses the full-prefix cache misses shown in `logs/usage.jsonl` after memory writes.

The colleague's note applies to splitting static instructions from volatile memory, keeping both cache markers, and checking cache creation and read counts. Its advice to keep tools stable also applies; the existing keyword-based tool selection remains in place, so a changed tool set can still cause a separate prefix miss. Top-N fact selection was not present and was not added. The note's token counts, savings estimate, and live API verification are not assumed for this bot.

Verified locally that a fact write changes only the second block, that both blocks have cache markers, and that `bot.py` compiles. No live Claude request was made, so actual cache hit and creation counts remain to be checked in `logs/usage.jsonl` on the next normal run.
