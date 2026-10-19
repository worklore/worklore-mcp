-- drafts.tokens_in / tokens_out are generated from the drafts.tokens JSON.
-- Review by Arhan Canli (dev.to, 2026-10-11): the first term had no coalesce,
-- so a row whose JSON lacked "input" got tokens_in = NULL instead of the cache
-- sum, and a value like "12.0" made the int cast raise and failed the whole
-- insert. A generated column can't be written around, so the expression must
-- never raise: numbers are parsed leniently ("12", "12.0", 12) and anything
-- else counts as missing.

create or replace function hb_json_int(v text) returns int
  language sql immutable parallel safe
as $$
  select case when v ~ '^\s*-?\d+(\.\d+)?\s*$' then round(v::numeric)::int end
$$;

-- NULL only when there is no token count at all; otherwise the sum of what's there.
alter table drafts alter column tokens_in set expression as (
  case when coalesce(hb_json_int(tokens->>'input'), hb_json_int(tokens->>'cache_read'),
                     hb_json_int(tokens->>'cache_write')) is null then null
       else coalesce(hb_json_int(tokens->>'input'), 0)
          + coalesce(hb_json_int(tokens->>'cache_read'), 0)
          + coalesce(hb_json_int(tokens->>'cache_write'), 0) end);
alter table drafts alter column tokens_out set expression as (hb_json_int(tokens->>'output'));
