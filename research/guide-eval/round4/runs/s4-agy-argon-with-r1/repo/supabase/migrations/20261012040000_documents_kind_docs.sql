-- Documentation pages (a site's /docs, /guide, /help, a repo's docs/ folder)
-- get their own kind, so a draft can point to them as "the docs" (Invite to
-- try: draft/materials.ts).
alter table documents drop constraint documents_kind_check;
alter table documents add constraint documents_kind_check
  check (kind in ('article', 'story', 'research', 'changelog', 'readme', 'faq', 'docs', 'fact', 'page'));
