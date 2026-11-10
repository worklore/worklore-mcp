# Deploy cleanup

Updated `deploy.sh` so the `site/` sync uses `--delete`, removing bucket files that were removed from `site/`. That sync excludes `s/*` and `a/*`, because those pages are built separately and uploaded with an explicit HTML content type.

After uploading the current pages, the script syncs each generated page prefix with `--delete`. This removes pages for deleted or private notes and authors with no remaining public notes. It creates both local prefix directories even when a build produces no pages, so an empty prefix is cleared too.

The colleague's note applies to the separate extensionless page uploads, their required HTML content type, and the risk that a root `--delete` sync would briefly remove every live page. Its proposed prefix exclusions and cleanup after upload apply here. The existing script did not already use `--delete`, so its specific outage was not occurring here.

Verified with `bash -n deploy.sh` and a local stub of `aws`: the recorded calls show the root sync excludes page prefixes, each page uploads before prefix cleanup, and both prefix syncs use `--delete`. No external deploy was run.
