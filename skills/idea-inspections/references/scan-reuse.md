# Reusing inspection scans

Reuse an audit snapshot only while the files, relevant dependencies, and IDE inspection
configuration remain unchanged. Audit itself makes no code edits, but another worker or
the user may have edited the project during triage.

For the Claude adapter, pass valid `snapshot` entries as `knownProblems` on the next run.
The direct route can reuse the same observations without that parameter. Reclassify them
against the current policy. Re-inspect after fixes instead of treating cached findings as
verification of the result.

Drop entries for changed files and affected dependents. Content hashes detect local edits,
but cannot detect a changed caller, classpath, or inspection profile. Invalidate broadly
when those dependencies are unknown. A changed-files-only pass cannot establish that
unchanged callers remain clean.

For optional cross-session reuse, store `{ "<file>": { sha, problems } }` in
`.idea-inspections/cache.json` and gitignore that cache. Keep `policy.yaml` eligible for
version control. Reuse only when the dependency and configuration context can also be
established; otherwise perform a fresh inspection.
