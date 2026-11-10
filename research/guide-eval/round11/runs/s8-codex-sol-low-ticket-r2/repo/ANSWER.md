# Cache fix

`build_system` now sends two text blocks, each with an ephemeral cache marker. The first is the byte-stable `INSTRUCTIONS` string. The second contains the date, athlete profile, zones, goal, facts, and language. A `save_fact` write changes only the second block, so the unchanged instruction prefix can be read from cache. Tool selection and the existing tool-use loop are unchanged.

The colleague's prefix-hashing explanation and two-marker split applied directly. Their advice to keep the static block free of dates and athlete fields also applied. The existing keyword-based tool filtering already works here, so I left it alone. Top-N fact selection was not needed: this bot continues to load all facts. The quoted token counts and cost percentages describe their bot, not measurements from this one.

I checked that both blocks have cache markers, that adding a fact changes only the second block, and that core tool selection still works. I did not make an API call, so actual cache-read token counts after this change are unverified. The existing `logs/usage.jsonl` shows full cache creation after each memory write before the fix; future usage entries can confirm the result.
