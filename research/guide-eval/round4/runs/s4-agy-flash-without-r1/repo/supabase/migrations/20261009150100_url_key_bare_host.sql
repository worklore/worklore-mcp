-- hb_url_key: a bare host ("worklore.dev/") means https://worklore.dev, like
-- the app's and read-landing's normalisation. Every stored url has a scheme,
-- so no stored url_key changes.
create or replace function hb_url_key(p_url text) returns text
language sql immutable parallel safe as $$
  select case
    when p_url is null or btrim(p_url) = '' then null
    else (
      with s as (
        select v.u, regexp_match(v.u, '^([a-zA-Z][a-zA-Z0-9+.-]*)://([^/?#]+)(.*)$') as m
        from (select case when btrim(p_url) ~ '^[a-zA-Z][a-zA-Z0-9+.-]*://' then btrim(p_url)
                          else 'https://' || btrim(p_url) end as u) v
      )
      select case
        when m is null then lower(regexp_replace(u, '/+$', ''))
        else lower(m[1]) || '://' || regexp_replace(lower(m[2]), '^www\.', '')
             || regexp_replace(regexp_replace(m[3], '#.*$', ''), '/+$', '')
      end
      from s
    )
  end
$$;
