-- Intent chips: "Discuss" (her view + one question that keeps the discussion
-- going, normal length) becomes the default chip. ask_feedback / ask_price
-- are no longer offered in the app but stay valid for existing drafts.
alter table drafts drop constraint drafts_intent_check;
alter table drafts add constraint drafts_intent_check
  check (intent in ('discuss', 'just_answer', 'invite_to_try', 'ask_feedback', 'ask_price', 'auto'));
