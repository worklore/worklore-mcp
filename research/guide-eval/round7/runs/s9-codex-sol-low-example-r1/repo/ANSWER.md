# Hidden story incident

The production 500 came from `StoryLibrary.hide`: its `UpdateExpression` used `hidden` as a bare attribute name. DynamoDB treats `hidden` as reserved and rejected the update with the `ValidationException` shown in `logs/prod-error.log`.

The staging story was successfully marked `hidden: true` by the manual CLI update. The public feed's `ProjectionExpression` also named `hidden` bare. In the read behavior reproduced by this repository's DynamoDB stand-in, that field was omitted from scanned items, so `not i.get("hidden")` evaluated true and let the story through. This explains why the manual write and redeploy did not fix the feed; the code shows no feed cache or second table.

All attribute names in the library's DynamoDB expressions now use `#` aliases with `ExpressionAttributeNames`, including conditions and the planned archive operation. Regression tests cover both hiding through the library and a story marked hidden directly in the table, then assert it is absent from the feed. `python3 -m unittest discover -s tests -v` passes (8 tests).

The colleague's note applied to the reserved `hidden` update failure, the projection/read failure, the convention of aliasing every expression attribute, and testing a record with `hidden` set. Its `similar` example did not apply to this codebase. The suggested deliberate bare-word experiments were unnecessary: the production log records the update rejection, and the existing fake plus regression test exercise the read behavior.
