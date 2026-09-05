# Inspection policy

The policy file is the project's decision, per inspection, about what to do with it. Each problem
the IDE reports is matched against the policy and assigned one **action**:

| Action     | Meaning                                                          | Code change? |
|------------|------------------------------------------------------------------|--------------|
| `ignore`   | Tolerated project-wide (the old "whitelist").                    | No           |
| `fix`      | Always fix it.                                                   | Yes          |
| `suppress` | Always suppress it at the occurrence (correct but intentional).  | Yes (annotation/comment) |
| `auto`     | Let the resolve agent decide fix vs suppress per the heuristics. | Maybe        |

Zero-tolerance still holds: a problem is never silently dropped unless a rule (or the default)
explicitly says `ignore`. Anything `fix`/`suppress`/`auto` that can't be safely resolved is reported
as **blocked**, not hidden.

## Location

```
.idea-inspections/
├── policy.yaml   # COMMITTED — the team's inspection policy
└── cache.json    # GITIGNORED — inspection-scan cache (see references/scan-reuse.md)
```

Add `.idea-inspections/cache.json` to `.gitignore`; keep `policy.yaml` committed.

## Why matching is on the message text

The JetBrains MCP `get_file_problems` returns only `{severity, description, lineContent, line, column}`
— there is **no inspection id**. So rules match on the `description` text (a regex), optionally
narrowed by `severity` and path globs. IntelliJ messages follow stable templates, so a regex over the
template (with variable parts wildcarded) is reliable.

## Schema

```yaml
# .idea-inspections/policy.yaml

# Action for any problem that no rule matches. Zero-tolerance default is "auto".
default: auto            # auto | fix | suppress | ignore

rules:                   # evaluated top-to-bottom; FIRST match wins
  - description: "^Duplicated code fragment \\(\\d+ lines long\\)$"   # regex over the message
    action: ignore
    reason: "Symmetric codec classes intentionally mirror each other."

  - description: "^Method '[^']*' is never used$"
    action: suppress
    suppressId: unused           # optional: the inspection id, used for @SuppressWarnings/@Suppress
    paths: ["**/api/**", "**/*Api.java"]   # optional: rule applies only under these globs
    reason: "Public API; suppress locally rather than delete."

  - description: "^Switch statement can be replaced with enhanced 'switch'$"
    action: fix
    reason: "Always modernize switches."
```

### Rule fields

- `description` — regex matched against the problem's `description`. Anchor with `^...$`. (A rule
  with no `description` matches every message — use only with `severity`/`paths` to scope it.)
- `action` — `ignore | fix | suppress | auto`. **Required.** (An unrecognized value is treated as
  `auto`, never as `ignore`, so a typo can't silently hide a problem.)
- `severity` — an IntelliJ severity (`ERROR`, `WARNING`, `WEAK_WARNING`, `INFO`, …). Optional; omit to
  match any.
- `paths` — list of globs (`**` spans directories, `*` stays within a segment). Optional; omit to
  match any file.
- `suppressId` — the inspection short name, used when `action: suppress`. Optional but helpful; the
  resolve agent otherwise infers it and verifies by re-inspecting.
- `reason` — human note; surfaced in reports and written as the suppression comment.

### Matching semantics

For each in-scope problem (every severity by default; restricted only when `--severity` is passed),
the **first** rule whose present fields all match wins; its
`action` applies. If no rule matches, the top-level `default` applies. Because it is first-match-wins,
put **specific or per-file rules above general ones** — e.g. a `paths: ["**/LegacyApi.java"]` rule
before a global rule for the same message gives that one file a different action.

### Per-file and global preferences

- **Global**: a rule with no `paths`.
- **Per directory / package / file**: add `paths`. A file-specific rule placed earlier overrides a
  later global rule for the same inspection.

## Building the policy (audit mode)

A fresh project has no policy. Running strict zero-tolerance immediately would try to fix/suppress
every warning, including the ones that should just be tolerated. **Audit mode** bootstraps the policy:

1. Inspect the scope; drop anything an existing rule already handles.
2. Aggregate remaining problems by inspection **type** (normalized message).
3. Triage each type (one agent per type) into a proposed rule: `ignore`, `fix`, or `suppress`
   (`mixed` → a path-narrowed rule plus "fix the rest").
4. Return `proposedRules` (ready to merge) and `byAction` counts. No code is edited.

The user accepts/trims, and the skill writes the rules to `policy.yaml`. Audit is **repeatable** —
already-covered types are excluded, so re-running it triages only inspections that appear later.

See `resolution-policy.md` ("Triage: choosing the action") for the criteria.

## How the skill consumes the policy

The main loop reads `.idea-inspections/policy.yaml` and passes `{ default, rules }` to the workflow as
`args.policy`. Classification (matching each problem to an action) happens in plain JavaScript — no
agent. Actionable problems carry their `pinnedAction` (`fix`/`suppress`/`auto`) into the resolve
stage, which honors it. A starter file is in `../assets/policy.example.yaml`.
