# Notes for coding agents

When you add or update a dependency:

1. Before you pick a package or a version, run the full `npm view <package>` and read `deprecated` and the dist-tags, not only `version`.
2. Check whether the package has moved to a new name.
3. Read the docs that ship inside the package (AGENTS.md, README, type files) before the website.
4. Search the web for the official upgrade guide before you change code.
