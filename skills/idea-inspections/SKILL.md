---
name: idea-inspections
description: Find and resolve IntelliJ inspections in scoped Java or Kotlin files using a live JetBrains IDE. Supports audit, dry-run, and policy-guided fixes.
---
# IntelliJ inspection sweep

Use a connected JetBrains IDE with the target project open. Resolve the scope before
calling its file-problem tool on one in-scope file. If the IDE or tool is unavailable,
report that blocker; other linters cannot establish IntelliJ inspection results.
Edits must target the project opened by the IDE, not a separate unobserved worktree.

## Scope and mode

Use `scripts/resolve-scope.sh` from this skill's actual absolute directory. Run it in
the target repository with one scope argument:

| Argument | Files |
| --- | --- |
| omitted or `changed` | Modified, staged, and untracked Java/Kotlin files versus HEAD |
| `all` | All tracked Java/Kotlin files |
| `module:<name>` or `dir:<path>` | Files under that directory |
| `package:<a.b.c>` | Files under that package, recursively |
| `file:<path>` | One file |

Honor a narrower natural-language scope. An empty file list needs no inspection.
Include all severities by default; `--severity=error` selects ERROR and
`--severity=warning` selects ERROR plus WARNING.

- `--audit`: inspect and propose policy rules, without code edits.
- `--dry-run`: inspect and propose per-problem changes, without edits.
- `--apply` or an explicit fix request: resolve actionable problems and verify them.

For broad scopes without a useful policy, start with policy triage to avoid mass
suppression of low-value warnings. Honor an explicit request to apply fixes. Do not
silently replace a fix request with an audit-only result; explain any unresolved policy
choice and continue safe independent fixes within the requested scope.

## Policy and resolution

Read `.idea-inspections/policy.yaml` when present. Read
[references/policy.md](references/policy.md) for matching and schema, and
[references/resolution-policy.md](references/resolution-policy.md) before resolving
problems. Match message text, severity, and paths; the first matching rule wins.
Each problem ends as fixed, narrowly suppressed with a reason, ignored by policy, or
reported as unresolved. Do not suppress a real defect just to achieve a clean count.

The policy encodes team decisions. Present concrete proposed rules before requesting
approval for policy changes. Existing approval of those rules is sufficient; do not ask
again. Keep unapproved policy suggestions separate from code fixes.

## Choose execution from available capabilities

Direct execution is sufficient for a small scope: inspect files through JetBrains MCP,
classify findings against policy, make the scoped fixes, and re-inspect affected files.
Use the actual tool schema rather than assuming a particular MCP prefix or edit API.

For larger scopes, available and authorized native subagents can own disjoint file sets.
Bound concurrency to the host's available capacity and the shared IDE's limits. Prefer
direct tool calls for inspection passthrough rather than creating an agent per call.
Avoid concurrent edits with cross-file dependencies.

When a compatible Claude Workflow tool is available and useful, read
[references/claude-workflow.md](references/claude-workflow.md) to invoke the bundled
`workflows/inspections.js`. Its absence does not block the direct route. Do not pass
Claude model names or environment variables to a different host.

Read [references/scan-reuse.md](references/scan-reuse.md) only when reusing a scan across
phases or runs. Invalidate changed files and affected dependents; a file hash alone does
not capture cross-file or IDE-configuration changes.

## Verify and report

Re-inspect resolved files and affected dependents. Review suppressions for correctness.
Apply the repository's formatter to the requested scope and build affected modules once
edits are ready; use the repository's required broader gate when applicable. Keep build
commands in the coordinating process rather than repeating them per worker.

Report fixes, suppressions and reasons, remaining problems, verification results, and
proposed policy changes. Claim a clean sweep only for the inspected scope with no
remaining policy-actionable findings. Stop retrying unchanged failures; report a concrete
blocker when no safe in-scope resolution remains.
