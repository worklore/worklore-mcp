# Cache fix

`build_system()` now puts the coaching instructions and stable athlete profile in a separately cached first block. The date and long-term facts are in a second block. After `save_fact`, the next request therefore keeps the same first cache breakpoint while sending the updated facts. The second breakpoint still lets unchanged context be reused across normal follow-up calls.

I added a short profile-use section to the instructions so the stable breakpoint remains above Claude Sonnet 4.5's 1,024-token minimum for prompt caching with the existing core tools. Tool selection and the memory persistence path are unchanged.

Verified locally that a fact write leaves the first block identical, changes the second block, and includes the new fact in the next request. I did not make a live API call, so actual cache usage after this change is not measured here.
