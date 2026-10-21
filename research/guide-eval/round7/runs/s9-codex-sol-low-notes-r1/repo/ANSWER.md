# Causes

- Hiding failed because `hide()` used the reserved DynamoDB attribute name `hidden` directly in its `UpdateExpression`. DynamoDB rejected the update with `ValidationException`, so the Hide action returned 500.
- The staging feed still showed the manually hidden story because `feed()` used `hidden` directly in its `ProjectionExpression`. The scan response omitted that attribute, so the Python filter treated the story as visible. The observed behavior comes from the expression, rather than a cache or a different table.

Both expressions now use `ExpressionAttributeNames` to alias `hidden`. Regression tests cover hiding through the library and a story whose `hidden` flag was set directly in the table.
