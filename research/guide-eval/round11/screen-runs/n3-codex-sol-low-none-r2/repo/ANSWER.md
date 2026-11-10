Updated `deploy.sh` to stage both `site/` files and generated note and author pages in `.build/deploy/`, then sync that complete set to S3 with `--delete`. A later deploy therefore removes bucket objects that the current build no longer produces, including deleted or private note pages, authors with no public notes, and removed `site/` files.

The script creates the pages directory even when no public pages are generated. It still uploads generated pages individually after the sync to set their HTML content type and cache control.

Verified locally with `bash -n`, `git diff --check`, and a mocked `aws` command that confirmed the sync includes `--delete` and page uploads retain their metadata. No deployment was run.
