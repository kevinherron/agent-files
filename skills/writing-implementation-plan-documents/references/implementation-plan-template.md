# [Feature Name]: Implementation Plan

[One- or two-sentence statement of the observable outcome this plan delivers.]

<!-- Cite authoritative sources by path, URL, issue, specification section, or dated
conversation. Link stable design sections instead of restating them. -->

Based on [authoritative source].

**Plan ID:** `[feature-slug]`
**Status:** [Ready | Conditional | Draft]
**Parent manifest:** [path or None]
**Grounded against:** [branch, commit, handoff, artifact version, or inspection date]
**Re-ground before:** [WPx and trigger, or None]

<!--
Ready: implementation can begin; no blocking decision remains and file-level grounding
is complete.
Conditional: implementation depends on a named handoff or code state; affected work
packages must be re-grounded before they start.
Draft: a material decision remains unresolved; do not use for unattended execution.

For a one-work-package plan touching only a handful of files, omit the TOC, Progress,
Implementation Map, Rejected Splits, and File Inventory when they add no navigation or
recovery value. Keep metadata, Scope, Current State, Desired End State, the work
package, verification, and any material open decision.
-->

* * *

## Table of Contents

<!-- Regenerate anchors after finalizing headings. Remove entries for omitted sections. -->

- [Progress](#progress)
- [Scope](#scope)
- [Current State](#current-state)
- [Desired End State](#desired-end-state)
- [Assumptions and Gaps](#assumptions-and-gaps)
- [Open Decisions](#open-decisions)
- [Prerequisites](#prerequisites)
- [Implementation Map](#implementation-map)
- [WP1 — Title](#work-package-1-title)
- [WP2 — Title](#work-package-2-title)
- [Rejected Splits](#rejected-splits)
- [File Inventory](#file-inventory)
- [Verification Summary](#verification-summary)
- [Downstream Handoff](#downstream-handoff)

## Progress

<!-- One checkbox per work package. Do not duplicate subtask or verification state here. -->

- [ ] [WP1 — Title](#work-package-1-title)
- [ ] [WP2 — Title](#work-package-2-title)

* * *

## Scope

<!-- Keep this aligned with the accepted design. State deliberate divergences. -->

This plan covers:

1. [Capability or migration outcome.]
2. [Capability or migration outcome.]

**Out of scope:**

- [Excluded behavior and where it is owned, if applicable.]

* * *

## Current State

<!-- Describe only the relevant baseline. Name exact existing files, APIs, schemas,
tests, or runtime seams. Link research for detailed history. -->

[What exists, what is missing, and the constraints that shape this implementation.]

* * *

## Desired End State

<!-- State observable behavior and the evidence that proves the entire plan complete. -->

[What users, callers, operators, or tests can observe when the plan is complete.]

* * *

## Assumptions and Gaps

<!--
Assumptions are bounded facts treated as given and where they can be confirmed.
Gaps are line-level choices that do not change public behavior, security, plan shape,
file ownership, or compatibility.
Omit when there are none.
-->

**Assumptions:**

- [Assumption and confirmation source.]

**Gaps:**

- [Bounded implementer choice and its allowed decision criteria.]

* * *

## Open Decisions

<!--
Required for Conditional or Draft plans when a material decision remains. Omit for a
Ready plan. Every decision needs an owner/source, trigger, affected work, and explicit
behavior if unresolved. Do not use anonymous or undated TBDs.
-->

| Decision | Owner or source | Resolve before | Affected work | If unresolved |
| --- | --- | --- | --- | --- |
| [Material decision] | [Person, design, specification, or code evidence] | [Trigger] | [WPx] | [Block, narrow scope, or safe fallback] |

* * *

## Prerequisites

<!-- List external plans, migrations, capabilities, tools, or permissions that must
exist. Omit if there are none. -->

- [Prerequisite and how to verify it.]

* * *

## Implementation Map

<!--
Show implementation-specific state/data flow, attachment seams, and package ownership.
If an accepted design already explains the architecture, link it and include only the
implementation delta. Omit when the work packages and exact file pointers are enough.
-->

### State and data flow

[Short numbered flow or compact narrative.]

### Attachment seams

- `[existing/path/File.ext]` — [how new behavior attaches].

### Planning decisions

<!-- Only sequencing, work-package, or implementation decisions not owned by a design. -->

- **[Decision].** [Chosen approach and why it best supports implementation.]

* * *

## Work Package 1: [Title]

[Capability or verified state this work package delivers and why it is ordered here.]

**ID:** `WP1`
**Depends on:** [Nothing, prerequisite, or stable work-package IDs]
**Done when:** [Observable acceptance contract]
**Checkpoint:** [Re-grounding action, or None]

### 1.1 [Subtask Title]

<!--
Use File for an existing file, New file for an intended new path, Artifact for a
non-code output, and Destination only in Conditional/Draft plans when an earlier
handoff determines the exact new path. Every Destination requires a Checkpoint.
Repeat a declaration when a subtask touches multiple files.
-->

**File:** `path/to/ExistingFile.ext`

[Describe the change, attachment seam, observable behavior, and important constraints.
Point to existing patterns instead of copying them.]

**New file:** `path/to/NewFile.ext`

[Describe the new artifact's responsibility and public shape.]

**Notes:**

- [Failure, cleanup, cancellation, concurrency, compatibility, or edge-case behavior.]
- [Security, privacy, permission, migration, or observability constraint when relevant.]

### 1.2 [Subtask Title]

**Artifact:** `path/to/generated-or-document-artifact`

[Describe the artifact and its consumers.]

### Design Decisions

<!-- Omit if this work package has no non-obvious local decision. Architectural
trade-offs belong in the design; cross-package sequencing belongs in the Implementation
Map. -->

- **[Decision].** [Chosen approach, alternatives considered, and why they lost.]

### Failure, Safety, and Security

<!-- Omit only when none of these concerns materially applies. Cover failure states,
rollback or cleanup, cancellation, permissions, privacy, trust boundaries, and unsafe
fallbacks at the level appropriate to this work package. -->

- [Failure or abuse case and required behavior.]

### Tests

**New file:** `path/to/TestFile.ext`

Tests:

- [Scenario, operation, and observable assertion.]
- [Failure or boundary scenario and assertion.]

### Verification

#### Automated

- [ ] Standard gate for `[package-or-module]` — commands in
  [Verification Summary](#verification-summary)
- [ ] [Work-package-specific check not covered by the shared gate.]

#### Agent review

<!-- Use for source inspection that is not yet automated, such as dependency direction
or forbidden coupling. Omit when unnecessary. -->

- [ ] [Invariant to inspect and evidence to record.]

#### Manual

<!-- Omit unless a genuinely human-only, subjective, physical-device, production, or
externally authorized check is required. State whether it blocks the next dependency. -->

- [ ] [Human action and observable result.] [Blocking / non-blocking]

### Rollout

<!-- Omit when normal merge/deploy is sufficient. Otherwise cover ordering, flags,
migration, rollback, and monitoring. -->

- [Rollout and rollback contract.]

### Implementation Notes

Filled in during implementation. Record dated deviations, surprises, and newly
discovered work. Update later work packages, readiness, open decisions, and the File
Inventory whenever a note invalidates them.

*None yet.*

* * *

## Work Package 2: [Title]

<!-- Repeat the complete work-package structure. -->

[Capability or verified state.]

**ID:** `WP2`
**Depends on:** `WP1` ([what it consumes])
**Done when:** [Observable acceptance contract]
**Checkpoint:** [Re-grounding action, or None]

* * *

## Rejected Splits

<!-- Omit when no plausible alternative split was considered. Record only boundaries
that would have produced dead code, broken intermediate behavior, untestable partial
work, forced rework, or repeated gates without a new capability. -->

- **[Rejected boundary].** [Why the chosen work-package boundary is better.]

* * *

## File Inventory

<!-- Derived from every File, New file, Destination, and Artifact declaration. Reconcile
it whenever the plan changes. Ready plans must not contain Destination rows. -->

| Path or destination | Work package | Change | Purpose |
| --- | --- | --- | --- |
| `module/src/main/.../ExistingFile.ext` | `WP1` | Modify | [Purpose] |
| `module/src/main/.../NewFile.ext` | `WP1` | New | [Purpose] |
| `[destination owned by prior handoff]` | `WP2` | Destination | [Purpose and trigger] |

* * *

## Verification Summary

<!-- Single home for shared commands. Prefer non-mutating checks. Put formatter apply
commands in Preparation unless repository policy explicitly makes them part of the
required gate. Do not repeat these command blocks in each work package. -->

### Preparation

```bash
[optional formatter or generator apply command]
```

### Standard affected-scope gate

```bash
[targeted tests]
[type, lint, or formatting check]
[affected package or module build]
```

### Final plan gate

```bash
[full required verification]
```

| Work package | Scope | Required evidence |
| --- | --- | --- |
| `WP1` | `[package-or-module]` | [Commands, tests, or artifact inspection] |
| `WP2` | `[package-or-module]` | [Commands, tests, or artifact inspection] |
| Final | full plan | [Final gate] |

* * *

## Downstream Handoff

<!-- Include when another plan consumes this one. Keep it concise. During initial
planning leave "Pending implementation"; during implementation replace it with final
contracts, deviations, verification evidence, downstream actions, and retained risks.
Omit when there is no downstream consumer. -->

*Pending implementation.*

When complete, record:

- **Public contracts and exact paths:** [Summary or links.]
- **Design deviations:** [Summary and rationale.]
- **Verification evidence:** [Commands and results.]
- **Downstream actions:** [Configuration or re-grounding required.]
- **Retained risks and unsupported behavior:** [Concise list.]
