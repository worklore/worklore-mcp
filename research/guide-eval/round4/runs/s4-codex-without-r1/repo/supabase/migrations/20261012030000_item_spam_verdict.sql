-- Spam check (triage route spam_check: the comment looks like a plug). Her
-- answer: 'spam' (hidden on the network from the app, item skipped) or
-- 'not_spam' (treated as a usual comment). null = not asked / not answered.
alter table items add column spam_verdict text check (spam_verdict in ('spam', 'not_spam'));
