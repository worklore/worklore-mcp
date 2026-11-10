# Deploy cleanup

`deploy.sh` now assembles a fresh `.build/deploy/` directory from `site/` and the generated note and author pages, then runs `aws s3 sync` with `--delete` against that complete build. Objects absent from the build, including deleted or private note pages and files removed from `site/`, are removed from the bucket on the next deploy. Extensionless pages are still uploaded with an explicit HTML content type and cache setting.

Verified with `bash -n deploy.sh` and a local build and staging run. No deployment was performed.
