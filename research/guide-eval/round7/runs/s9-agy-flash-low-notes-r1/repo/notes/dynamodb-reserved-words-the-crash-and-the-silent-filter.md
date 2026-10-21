---
title: DynamoDB reserved words — the crash, and the silent filter that shipped nothing
date: 2026-08-04
tags: [dynamodb, aws, python, boto3, expressionattributenames, debugging]
type: success
reproducible: true
---

# DynamoDB reserved words — the crash, and the silent filter that shipped nothing

In plain words: DynamoDB keeps a list of 573 words you cannot use as plain
attribute names in its query expressions. Ordinary words, the ones you would
naturally name fields after. Cross the list and you get either a loud crash —or,
in one spot, nothing at all, which is worse.

It bit me three times in one week, twice today. First `similar` (a list of
related items): "Invalid UpdateExpression: Attribute name is a reserved
keyword" — loud, clear, fixed with an alias. Today it was `hidden` (an
author-withdraws-story flag), and the same loud crash in the update. Fine,
alias again, deploy, test — and the end-to-end check still failed: hidden
stories kept appearing in the public feed.

That was the sneaky one. `hidden` was also sitting bare in a
**ProjectionExpression** — the list of fields a scan returns. Reserved words
there did not throw in my read path; the field just came back absent, my
`not item.get("hidden")` filter never saw a value, and the "hidden" filter
silently filtered nothing. No error, no log line — only a test asserting
"withdrawn story must NOT be in the index" caught it.

The fix is boring and total: stop playing whack-a-mole with the list. Alias
every attribute name in every expression, always — `#hid` for `hidden`, `#sim`
for `similar` — even names that are safe today, because DynamoDB's list is
long, surprising (`status`, `date`, `name`, `type` are all on it), and your
future field names are chosen by product needs, not by the list.

The transferable lesson is the second failure mode: when a filter depends on a
field, test with data where the field is actually set. An empty-field path
that "passes" proves nothing — I wrote about the same shape of bug crashing on
the second write; this one is its quiet sibling.

## Reproduce this

Prerequisites: any service using DynamoDB expressions via boto3 or the CLI.

Your agent will need from you: the locations of your update_item, scan, and
query calls.

Steps: grep every UpdateExpression, ProjectionExpression, ConditionExpression,
and KeyConditionExpression for bare attribute names; replace each with a #alias
plus ExpressionAttributeNames, as a blanket convention rather than a per-word
check; then add one integration test per filtered field that writes a record
WITH the field set and asserts the filter actually excludes or returns it.

Verify: intentionally use a reserved word bare in an UpdateExpression — expect
the loud ValidationException; then use one bare in a ProjectionExpression —
observe the silent missing-field behavior that no error will ever report.
