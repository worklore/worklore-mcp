# Prompt cache fix

`build_system()` now sends the stable coaching instructions as the cached first system block and the athlete's current profile and facts as a separate, uncached block. A `save_fact` changes only the second block, so the next tool round can reuse the instruction prefix while seeing the newly saved fact.

I expanded the stable instructions with practical guidance already implied by the existing rules. This keeps the reusable prefix large enough for Claude Sonnet's 1,024-token prompt-cache minimum. Tool selection remains unchanged.

Verified locally that the cached block is identical before and after adding a fact, while the athlete block updates and has no cache marker. I did not make an API call, so actual cache-read usage has not been measured. Different selected tool sets can still produce distinct cache prefixes.
