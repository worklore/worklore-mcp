-- Like from the thread screen: the phone likes the comment on the network
-- (dev.to POST /reactions, with her session) and records it here so the
-- button shows it. null = not liked from Hearback.
alter table items add column liked_at timestamptz;
