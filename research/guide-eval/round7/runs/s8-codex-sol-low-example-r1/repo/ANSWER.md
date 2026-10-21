# Prompt cache fix

Changed `build_system()` in `bot.py` to send two text blocks, each with an ephemeral cache marker. The first contains only the constant coaching instructions; the second contains the date and athlete context, including long-term facts. After `save_fact`, the instruction block remains byte-identical, so a changed fact only invalidates the later cache segment.

The colleague's two-segment approach applies directly. Their advice to keep tool schemas stable also applies: this bot already keeps the selected tools fixed throughout each message's tool loop, so I left its existing keyword filtering unchanged. The warning about per-message fact selection applies, but this bot already includes all facts. Usage logging already records cache creation and read tokens, so it needed no change.

Verified locally that a fact update changes only the second block and that both blocks have cache markers; `bot.py` also compiles. I did not make live Claude calls, so the exact cache read and creation token counts after this change remain unmeasured.
