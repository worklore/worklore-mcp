# Hidden story still in the public feed (staging)

Date: 2026-08-05
Reporter: Dasha (content)
Environment: staging, table `stories-staging`, build 2026-08-04 (same as prod)

The Hide button on staging gives a 500 (same error as prod, see
prod-error.log), so I hid "my-first-week" by hand with the AWS CLI:

    aws dynamodb update-item --table-name stories-staging \
      --key '{"slug":{"S":"my-first-week"}}' \
      --update-expression 'SET #h = :t' \
      --expression-attribute-names '{"#h":"hidden"}' \
      --expression-attribute-values '{":t":{"BOOL":true}}'

`get-item` afterwards shows `hidden: true` on the item, so the write landed.
But `GET /feed` on staging still lists "my-first-week" -- ten minutes later,
after a redeploy, and in a private browser window. Nothing in the logs,
no error, the feed call returns 200.

Is the feed cached somewhere? Or does the feed read from a different table?
