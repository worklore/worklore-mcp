# Deployment cleanup

Updated `deploy.sh` so the `site/` sync uses `--delete`, removing bucket files that have been removed from `site/`. The sync excludes `s/*` and `a/*`, because generated note and author pages are uploaded separately with an explicit HTML content type. After those uploads finish, the script lists both page prefixes and deletes keys absent from the current build. A deleted or private note therefore loses its page on the next deploy; an author page also disappears when that author has no public notes left.

The colleague's warning applies: a root-level `sync --delete` would temporarily remove every generated page before its separate upload. The prefix exclusions and cleanup after upload apply here. The note's `paths/` prefix does not apply to this project. I kept the existing individual uploads so extensionless pages retain their HTML content type.

Verified locally with `bash -n deploy.sh`, `python3 -m py_compile build_pages.py`, and `git diff --check`. No deployment or external service was used.
