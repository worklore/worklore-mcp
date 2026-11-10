# Deploy cleanup

Updated `deploy.sh` so the `site/` sync uses `--delete`. Files removed from `site/` are therefore removed from the bucket on the next deploy.

The sync excludes `s/*` and `a/*`, which are produced separately by `build_pages.py`. The script uploads those pages with their existing HTML content type, then lists both bucket prefixes and deletes keys absent from the current build. This removes pages for deleted or private notes, plus author pages with no remaining public notes. The page cleanup lists every page before deleting, including paginated S3 results.

The colleague's note applies to the split upload: a plain `sync --delete` would temporarily remove every current note and author page before the separate upload restored it. Its exclusion and post-upload cleanup approach applies here. Its `paths/` prefix and post-upload `sync` suggestion do not apply: this build produces only `s/` and `a/`, and syncing extensionless pages could change their HTML content type.

Checked `bash -n deploy.sh`, ran `build_pages.py` locally, and checked `git diff --check`. No live deploy was run.
