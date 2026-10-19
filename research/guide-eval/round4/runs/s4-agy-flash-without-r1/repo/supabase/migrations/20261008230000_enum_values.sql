-- New enum values for the v1 screens (docs/API.md). Own migration: a value
-- added by ALTER TYPE can't be used in the same transaction.
--   person_stage: the design's four people tabs are Talked (talking),
--   Gave feedback, Wants to try (would_try), Would pay.
--   item_kind: a post found by Discover, not addressed to the founder.
alter type person_stage add value if not exists 'gave_feedback' after 'talking';
alter type person_stage add value if not exists 'would_pay' after 'would_try';
alter type item_kind add value if not exists 'post';
