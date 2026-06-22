# Resolution policy

Every in-scope problem — by default **every severity** (`ERROR`, `WARNING`, `WEAK_WARNING`, `INFO`, …;
narrow with `--severity`) — gets exactly one resolution:

| Resolution   | What it means                                                | Where it lives        |
|--------------|--------------------------------------------------------------|-----------------------|
| **ignore**   | Tolerated project-wide by policy. No change.                 | a rule in `.idea-inspections/policy.yaml` |
| **fix**      | Change the code so the warning is gone.                      | The source file       |
| **suppress** | Correct report, intentional code here — silence this spot.   | An annotation/comment in the source |
| **blocked**  | Neither a safe fix nor a verifiable suppression is possible. | Reported to the user, not silenced |

Which resolution applies is set by the policy's matching rule (`action: ignore|fix|suppress`) or, when
no rule pins it (`action: auto` or the `default`), chosen by the resolve agent per the guidance below.
Zero-tolerance means a file is "clean" only when it has **no** policy-actionable problems left, of any
severity (`WEAK_WARNING` and `INFO` included, not just `WARNING`/`ERROR`). `blocked` is the honest escape hatch — it never claims success.

## Choosing between fix and suppress

**Default to fix.** Suppress only when all of these hold:

1. The inspection is *correct* (not a false positive about the code's actual behavior).
2. The code is *intentional* the way it is, here, specifically.
3. A fix would make the code worse, change a real contract, or is otherwise inappropriate.

When suppressing, use the **narrowest scope** and add a one-line reason. When fixing a problem that
indicates a *real defect* (not a style nit), keep the change minimal and correct — and if the right
behavior is genuinely ambiguous (it changes a public nullness/throws contract, or deletes code that
may be load-bearing), mark it **blocked** for a human rather than guessing.

## Triage: choosing the action (audit mode)

Audit mode recommends, per inspection *type*, a policy action — `ignore`, `fix`, `suppress`, or
`mixed`. The test is the inspection's **signal in this codebase**, not just its name:

**Lean `ignore` (questionable value / accepted by policy):**

- Subjective or stylistic: `Duplicated code fragment …`, `Field '…' may be 'final'`,
  `'Optional<…>' used as type for parameter '…'`.
- Structural by design: symmetric generated/codec classes flagged as duplicates.
- Unused *public-API* declarations (`Method '…' is never used` on exported types) — `ignore` or
  `suppress`, **narrowed by `paths`** to the API surface so genuinely dead private code is still caught.

**Lean `fix`/`suppress` (genuine issue) — never `ignore`:**

- Correctness / bug smells: `Condition '…' is always 'true'/'false'`,
  `Passing 'null' argument to parameter annotated as @NotNull`, resource leaks,
  `… is never thrown` on a non-API method.

**Judgment call (default `fix`, `ignore` only to avoid churn):**

- Mechanical simplifications: enhanced `switch`, `assertInstanceOf`, `!isEmpty()`. Default to `fix`;
  `ignore` only if the team explicitly prefers to avoid the churn (mark `questionableValue`).

A type that is legitimate in some locations and noise in others is **mixed**: propose a path-narrowed
`ignore`/`suppress` rule for the noisy locations and let the rest be fixed.

## Suppression syntax

The MCP does not return the inspection id, but suppression requires it. Infer the id from the
message (table below), apply the suppression, then **verify by re-inspecting** — the re-inspection is
the oracle. If the problem persists, the id was wrong: try an alternate, or fall back to a fix.

Java:

```java
@SuppressWarnings("unused")             // on the smallest element: local, param, method, field, type
// or, for a single line, directly above it:
//noinspection unused
```

Kotlin:

```kotlin
@Suppress("unused")
//noinspection unused
```

`@SuppressWarnings`/`@Suppress` take the inspection id; `//noinspection` takes the same id and is the
fallback when no annotatable element is in range (e.g. inside an expression or a comment-only spot).

## Message → inspection-id / default resolution

These are the real IntelliJ messages observed in this codebase, the likely suppression id, and the
default resolution. Verify the id by re-inspecting after suppressing.

| `description` template                                            | Likely id                  | Default            |
|-------------------------------------------------------------------|----------------------------|--------------------|
| `Parameter '…' is never used`                                     | `unused`                   | fix (drop param) — suppress if an override/SAM/framework signature requires it |
| `Method '…' is never used` / `… is never used`                    | `unused`                   | fix (delete) if private; suppress `@SuppressWarnings("unused")` + reason if it's public API; an `ignore` policy rule if API-wide |
| `Field can be converted to a local variable`                      | `FieldCanBeLocal`          | fix                |
| `Field '…' may be 'final'`                                        | `FieldMayBeFinal`          | fix                |
| `'…' used without 'try'-with-resources statement`                 | `resource`                 | fix (wrap) — suppress if a test lifecycle owns the resource |
| `Switch statement can be replaced with enhanced 'switch'`         | `EnhancedSwitchMigration`  | fix                |
| `'assertTrue()' can be simplified to 'assertInstanceOf()'`        | `SimplifiableAssertion`    | fix                |
| `'…' can be replaced with '…'` / `… can be simplified to …`       | varies (simplification)    | fix                |
| `Exception '…' is never thrown in the method`                     | `RedundantThrows`          | fix (drop throws) — suppress if it pins a public contract |
| `Value of parameter '…' is always '…'`                            | `unused` / constant-param  | suppress if the constant is intentional in a test helper; else fix |
| `Write-only object` / `… is never read`                           | `unused`                   | fix                |
| `'Optional<…>' used as type for parameter '…'`                    | `OptionalUsedAsFieldOrParameterType` | fix (take the unwrapped value) — suppress if the API deliberately accepts Optional |
| `Passing 'null' argument to parameter annotated as @NotNull`      | `ConstantConditions` / `NullableProblems` | **fix** — likely a real bug; review carefully, do not suppress |
| `Condition '…' is always 'true'/'false'`                          | `ConstantValue`            | **fix** — remove the dead branch, or treat as blocked if it reveals a contract problem |
| `Calls to boolean method '…' are always inverted`                 | `BooleanMethodIsAlwaysInverted` | fix (invert the method) or suppress if intentional |

This table is a starting point, not exhaustive. For an unfamiliar message, reason about what the
inspection is reporting, prefer a behavior-preserving fix, and always confirm with a re-inspection.

## Project conventions to respect when fixing

Read `AGENTS.md` / `CLAUDE.md` at the project root before editing. For this codebase specifically:

- It is a JSpecify `@NullMarked` project. `@Nullable` annotates fields, parameters, returns, and
  type arguments — **never local variables**. Narrow nullness on locals with `requireNonNull` /
  `assertNotNull` instead.
- Keep diffs minimal; do not reformat unrelated lines. `mvn spotless:apply` runs once after the
  workflow (in the main loop), so leave formatting to it.

## The verify loop (mandatory)

After resolving a file, the resolver re-runs `get_file_problems` and reports anything still present.
A separate, adversarial verify agent then re-inspects from scratch and reviews soundness — it
specifically challenges each suppression ("is this a masked bug?") and confirms each fix preserves
behavior. A file is only reported as resolved when the re-inspection is clean **and** the verifier
approves.
