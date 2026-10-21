# Hidden stories: causes and fix

## Causes

- The hide operation put `hidden` directly in its `UpdateExpression`. The production log shows DynamoDB rejecting that reserved attribute name with a `ValidationException`, so the hide request returned 500 and did not set the flag.
- The feed scan also put `hidden` directly in its `ProjectionExpression`. In this repository's DynamoDB stand-in, that projection omits the reserved field from returned items. The feed then evaluates `not item.get("hidden")`; a missing field passes that check. This explains why the story manually marked `hidden: true` in staging could still appear. The code provides no cache or second-table path for the feed; it scans the library's table.
- The existing tests only covered stories with no `hidden` field. They could not catch a broken projection or the hide update. A separate bare `status` in the archive condition was another reserved-name failure waiting to happen.

## Fix and verification

Every attribute name in this module's DynamoDB expressions now uses an `ExpressionAttributeNames` alias, including condition, update, and projection expressions. The feed still omits story bodies and excludes items whose projected `hidden` value is true.

Regression tests now cover hiding through the library, a story marked hidden directly in the table (as in the staging report), and the archive condition. `python3 -m unittest discover tests -v` passes all 8 tests. No live AWS call or deployment was made.

## Colleague's note

The reserved-name diagnosis for the hide update, the risk of a missing `hidden` value in the feed projection, the convention to alias all expression attribute names, and the advice to test with the field actually set all applied here. The `similar` example did not apply: this module has no `similar` attribute. The note's suggested deliberate failing calls were unnecessary because the production log already records the update failure and the regression tests exercise the read failure in this repository's stand-in. The claimed behavior of a live DynamoDB projection was not independently verified against AWS here.
