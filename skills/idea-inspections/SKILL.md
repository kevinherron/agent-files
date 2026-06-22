---
name: idea-inspections
description: >-
  This skill should be used when the user asks to "fix inspections", "find IntelliJ inspections",
  "clean up IDE warnings", "run an inspection sweep", "fix IDEA code inspections", "resolve
  inspection warnings", or otherwise wants to find and fix/suppress JetBrains IntelliJ code
  inspections in Java/Kotlin files across a scope (a file, package, Maven/Gradle module, all files,
  or git-changed files) using the jetbrains MCP server. Applies a zero-tolerance fix / suppress /
  ignore resolution to every warning, governed by a configurable per-inspection policy file that pins
  ignore/fix/suppress globally or per path, and orchestrates the work with dynamic workflows.
argument-hint: "[changed|all|module:<m>|package:<p>|file:<f>] [--audit|--dry-run|--severity=error]"
compatibility: >-
  Requires a JetBrains IDE (IntelliJ IDEA) running with the target project open and the `jetbrains`
  MCP server connected. Inspections run against the live IDE, so edits touch the real project files.
---

# IntelliJ inspection sweep

Find and resolve IntelliJ IDEA code inspections in Java/Kotlin files using the `jetbrains` MCP
server, orchestrated as a **dynamic workflow** that fans out one slice per file. This skill is
authorized to launch the Workflow tool.

Operating stance is **zero tolerance**: every in-scope problem ends as one of —

- **fix** — change the code so the warning is gone,
- **suppress** — a narrow `@SuppressWarnings` / `@Suppress` / `//noinspection` with a reason, when
  the report is correct but the code is intentional here,
- **ignore** — the inspection is tolerated project-wide by the policy (no change),
- **blocked** — neither a safe fix nor a verifiable suppression is possible; surfaced to the user,
  never silently left.

The **policy** (`.idea-inspections/policy.yaml`) decides which action applies to each inspection —
`ignore`, `fix`, `suppress`, or `auto` (let the agent choose fix vs suppress). A file is clean only
when it has no policy-actionable problems left. **Every inspection severity is in scope by default** —
`WEAK_WARNING` and `INFO` count, not just `WARNING`/`ERROR` (those lower severities are where
maintainability smells like duplicate switch branches and collapsible `if`s show up). Narrow the
scope only with the `--severity` flag.

## Prerequisites

Inspections come from the live IDE. Before doing anything, confirm the IDE is up: call
`mcp__jetbrains__get_file_problems` on any one in-scope file. If it errors (no IDE / project not
open), stop and ask the user to open the project in IntelliJ IDEA. Because the IDE inspects the real
project files, edits are made on the working tree (not a git worktree) — they are git-reversible.

## Scope

Parse the scope from the skill argument. Grammar (the token is the first argument):

| Argument            | Scope                                                              |
|---------------------|-------------------------------------------------------------------|
| *(none)* / `changed`| Java/Kotlin files changed vs HEAD (modified + staged + untracked) — **default** |
| `all`               | Every tracked Java/Kotlin file                                    |
| `module:<name>`     | Files under a Maven/Gradle module dir, e.g. `module:iec104-core`  |
| `package:<a.b.c>`   | Files under that package (recursive), e.g. `package:com.foo.bar`  |
| `dir:<path>`        | Files under a directory (recursive)                               |
| `file:<path>`       | A single Java/Kotlin file                                         |

Optional flags: `--audit` (build the policy by triaging inspection types, no edits — see below),
`--dry-run` (inspect and propose per-problem fixes, no edits), `--apply` (force apply),
`--severity=error` / `--severity=warning` (narrow the scope to `ERROR` only, or `ERROR`+`WARNING`).
By default **all** inspection severities are in scope (`WEAK_WARNING`, `INFO`, …); `--severity` is the
only way to restrict that.

Resolve the scope to a concrete file list with the bundled script — do not hand-roll the globbing:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/resolve-scope.sh" "<scope-arg>"
```

It prints project-relative `.java`/`.kt` paths, one per line. An empty list means nothing to do —
report that and stop.

## Load the policy

Read `.idea-inspections/policy.yaml` (relative to the project root) if it exists, and pass it as
`{ default, rules }`. **Never edit the policy without the user's approval** — it encodes team decisions.

If the policy is **absent or thin** (a first run on an existing codebase), do not jump straight to
strict resolution — that would try to fix/suppress every low-value warning instead of letting the
project decide what to tolerate. Recommend **audit mode** first (default to it for broad scopes —
`all`, `module:`, `package:`, `dir:`; for a single `file:` scope, strict resolution is fine even with
no policy). Audit builds the policy; later apply runs resolve what's left.

Rules match on the problem **message text** (a regex over `description`), optionally narrowed by
`severity` and path globs — because the MCP returns no inspection id — and assign an action
(`ignore`/`fix`/`suppress`/`auto`); first match wins, and a problem no rule matches takes `default`
(default `auto`). See `references/policy.md` for the schema and matching rules, and
`assets/policy.example.yaml` for a starter file to offer when none exists.

## Run the workflow

Launch the bundled, parameterized workflow once with the resolved inputs:

```
Workflow({
  scriptPath: "${CLAUDE_SKILL_DIR}/workflows/inspections.js",
  args: {
    projectPath: "<absolute project root>",
    files: [ ...resolved project-relative paths... ],
    policy: { default: "auto", rules: [ ...from policy.yaml... ] },
    mode: "apply",                     // "apply" | "dry-run" | "audit"
    severityFloor: ["ALL"],            // every severity (default); ["ERROR","WARNING"] or ["ERROR"] per --severity
    policyDoc: "${CLAUDE_SKILL_DIR}/references/resolution-policy.md",
    knownProblems: { },                // optional: reuse a prior scan (see "Reusing the scan")
    inspectModel: "sonnet"             // cheap model for the inspect passthrough (default; "haiku" = cheapest)
  }
})
```

Every run returns `snapshot` (file → problems for every in-scope file). Hold onto it — it is what
lets the next phase skip re-inspection (see below).

#### Passing inputs robustly

`args` must reach the script as a **real JSON object**, not a JSON-encoded string. A large inline
`args` payload (a full `all` file list, or a big `knownProblems` cache) can get stringified or dropped
at the tool boundary; the symptom is the run logging "No files in scope" and falling back to mode
`apply`. The script now re-parses a stringified `args` defensively and logs loudly if inputs are
missing, but the bulletproof option for **large scopes** is to embed the inputs in the script text and
delegate to the bundled workflow via the inline `workflow()` hook — then only script text crosses the
boundary, never a structured payload:

```
Workflow({ script: `
export const meta = { name: 'idea-inspections-run', description: 'Run the inspection workflow with embedded inputs' }
const inputs = {
  projectPath: "<absolute project root>",
  files: [ /* resolved project-relative paths */ ],
  policy: { default: "auto", rules: [ /* from policy.yaml */ ] },
  mode: "audit",
  severityFloor: ["ALL"],
  policyDoc: "${CLAUDE_SKILL_DIR}/references/resolution-policy.md"
}
return await workflow({ scriptPath: "${CLAUDE_SKILL_DIR}/workflows/inspections.js" }, inputs)
` })
```

Use the direct `scriptPath` + `args` form for small scopes (`changed`, `file:`, a small module); use
the wrapper for `all` or any run with a large `files`/`knownProblems` payload.

`${CLAUDE_SKILL_DIR}` expands to this skill's absolute directory when the skill loads, so those paths
resolve automatically — no manual path editing. In `apply`/`dry-run` mode the workflow
pipelines each file through **Inspect** (cheap `get_file_problems`) → **Resolve** (fix/suppress each
policy-actionable problem via `mcp__jetbrains__replace_text_in_file`, then re-inspect) → **Verify** (an
independent, adversarial re-inspection + soundness review that challenges every suppression).
Policy classification happens in plain JavaScript between Inspect and Resolve — no agent; each
actionable problem carries its `pinnedAction` (fix/suppress/auto) into Resolve, which honors it.

The **Inspect** agents run on a cheap model (`inspectModel`, default Sonnet) — they only load the MCP
tool and return its output, so paying for the session model on every file is pure waste. **Resolve**
and **Verify** inherit the session model (that is where the real reasoning lives); override per stage
with `resolveModel` / `verifyModel` / `triageModel` if needed.

Details of the orchestration live in `workflows/inspections.js`; the fix/suppress judgment and the
message→inspection-id cheat sheet the resolve agents rely on live in `references/resolution-policy.md`.

### Modes

- **`apply`** (default) — resolve every policy-actionable problem (fix/suppress per its
  `pinnedAction`), then verify. Returns `clean`, `resolvedOk`, `needsAttention`, `errored`,
  `policySuggestions`.
- **`dry-run`** (`--dry-run`) — same Inspect + policy classification, but stop at a per-problem plan
  (`dryRunPlans`, each carrying its `pinnedAction`); no edits. Present it, and on confirmation re-run
  with `mode: "apply"`.
- **`audit`** (`--audit`) — bootstrap/grow the policy. See below.

### Audit mode: bootstrapping the policy

For a first run (or to grow the policy later), use `mode: "audit"`. It inspects the scope, aggregates
the actionable problems by inspection **type** (normalized message), and fans out one triage agent per
type that recommends a policy action — **ignore** (low-signal/subjective/noise or accepted by policy),
**fix**/**suppress** (a genuine issue), or **mixed** (path-narrowed). Types already covered by the
current policy are excluded, so audit is repeatable as new inspections appear. It edits nothing and
returns:

- `proposedRules` — ready-to-merge policy rules (`description` regex + `action` + optional
  `paths`/`suppressId`/`reason`), each with occurrence counts and examples,
- `byAction` — counts of proposed rules per action (ignore/fix/suppress),
- `types` — every triaged type with its rationale and examples.

Present these grouped by action, let the user accept/trim, then **write the accepted rules to
`.idea-inspections/policy.yaml`** (create it, or merge — dedupe by `description` regex). After the
policy exists, run `mode: "apply"` (commonly on `scope:all` or per module) to resolve everything not
ignored — reusing the audit scan as described next, so it does not rescan.

### Reusing the scan — don't rescan between phases

The inspect pass is the expensive part of a large run, and **audit makes no edits**, so its scan stays
valid afterward. To go from audit straight into fixing without rescanning, pass the audit's `snapshot`
back as `knownProblems` on the follow-up `apply` run. Files present in `knownProblems` are not
re-inspected, so apply only spends agents on files that actually have actionable problems. Correctness
holds because each resolve agent still re-inspects the one file it edits (its verification oracle).

In-session continuation (the common first-run flow):

1. `mode:"audit"` over the scope → triage → write the approved policy.
2. `mode:"apply"` over the same scope with `policy:` (updated) and `knownProblems:` (the audit
   `snapshot`). No second scan; only dirty files get resolve/verify agents.

**Invalidate edited files.** A file changed since it was scanned must be dropped from `knownProblems`
so it re-inspects. Key the cache by content hash (`git hash-object <file>`) and drop entries whose
hash changed — the files apply just edited then re-inspect themselves on the next run automatically.

**Cross-session / incremental reuse (optional).** Persist `snapshot` to `.idea-inspections/cache.json`
as `{ "<file>": { sha, problems } }`, and **gitignore it** (add `.idea-inspections/cache.json` to the
project `.gitignore` — the sibling `policy.yaml` stays committed). On a later run, load the cache,
drop entries whose current `git hash-object` differs, and pass the survivors as `knownProblems`. This
makes routine `scope:changed` runs nearly free — only the handful of changed files are inspected.

**Cross-file caveat.** Some inspections depend on other files (e.g. "method never used" flips when a
caller appears or disappears), so one apply pass over a huge scope is not a guaranteed fixpoint. After
a big apply, run `apply` again on `scope:changed` until it reports clean — cheap (only files you
touched) and it absorbs cross-file fallout.

### Scale note

On a cold run each in-scope file spends one Inspect agent on the cheap `inspectModel` (Sonnet by
default, not the session model); dirty files add a Resolve and a Verify agent on the session model. A
whole-repo `all` sweep over hundreds of files is therefore a large, billable run the first time — but
the inspect pass is cheap-model work, and a `knownProblems` cache hit costs nothing, so warm runs only
pay for files that are new, changed, or actually dirty. Prefer `changed`, `module:`, or `package:` scopes for routine use and
reserve a full `all` scan for the first audit or a deliberate sweep. The IDE is a single shared
instance, so agents edit the real project files (no worktree isolation).

## After the workflow (apply mode)

Run these once in the main loop — do not have the per-file agents run Maven:

1. `mise exec -- mvn spotless:apply` — apply formatting (the agents leave formatting alone).
2. Compile/build the affected modules to confirm fixes didn't break anything, e.g.
   `mise exec -- mvn -q -pl <module> -am test-compile` (or `clean verify` for a full check).
3. `git diff --stat` — summarize what changed so the user can review/revert.

## Report and approval gates

**apply / dry-run:** summarize per outcome — files cleaned, problems fixed vs suppressed (with the
suppression reasons), and anything in `needsAttention` (**blocked** problems, problems still
**remaining** after edits, or resolutions the verifier did **not approve**). Present these plainly; do
not claim a clean sweep when any remain. Then surface `policySuggestions` (inspections recurring
across ≥ 3 files) as *candidate* policy rules — pin them to `fix`/`suppress`/`ignore` so `auto` doesn't
re-decide them every run.

**audit:** present `proposedRules` grouped by action (with rationale and example occurrences) and the
`byAction` counts, so the user sees what would be tolerated, fixed, and suppressed. Let them accept or
trim.

**Writing the policy is the only edit gated on approval.** After the user approves rules (from audit's
`proposedRules` or apply's `policySuggestions`), write them to `.idea-inspections/policy.yaml` — create
the dir and file from `assets/policy.example.yaml` if absent, or merge into the existing `rules:` list,
de-duping by `description` regex. Never add rules the user did not approve.

## Resources

- **`scripts/resolve-scope.sh`** — turn a scope argument into a Java/Kotlin file list.
- **`workflows/inspections.js`** — the parameterized Inspect → Resolve → Verify workflow.
- **`references/policy.md`** — policy schema (default + rules, actions), message-text matching, file location.
- **`references/resolution-policy.md`** — fix vs suppress vs ignore, suppression syntax, and the
  message→inspection-id cheat sheet (the resolve agents read this).
- **`assets/policy.example.yaml`** — conservative starter policy to offer a project.
