# Deploy cleanup

`deploy.sh` now stages both `site/` and the generated note and author pages, then syncs that complete build to S3 with `--delete`. A later deploy therefore removes bucket objects for deleted or private notes, authors with no public notes, and files removed from `site/`. The separate page uploads still set the HTML content type and cache control for extensionless page keys.

The page build now creates its output directory even when there are no public pages.

Verified locally with `bash -n deploy.sh`, `git diff --check`, and a run using a mocked `aws` command. The mock captured the sync with `--delete` and the page uploads. No deployment was performed.
