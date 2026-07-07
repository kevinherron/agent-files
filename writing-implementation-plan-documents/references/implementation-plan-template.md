# [Feature Name]: Implementation Plan

[One- or two-sentence summary of what this plan implements.]

<!-- State the plan's source.
Replace the "Based on [source]." line below with whichever of these applies:
- Based on the design in `docs/design/[feature-slug].md`.
- Based on research in `docs/research/[research-doc].md`.
- Based on [specification name, section reference].
- Based on [issue tracker link].
- Based on requirements discussed with [user] in conversation ([date]).
-->

Based on [source].

* * *

## Table of Contents

<!-- After filling in the phase titles, regenerate every anchor from the final heading
text (GitHub slug rules: lowercase, punctuation stripped, spaces become hyphens —
"Phase 1: Data Model" becomes #phase-1-data-model).
Remove the entry for any section you omit.
One "Phase N" entry per phase.
-->

- [Progress](#progress)
- [Scope](#scope)
- [Current State](#current-state)
- [Desired End State](#desired-end-state)
- [Assumptions and Gaps](#assumptions-and-gaps)
- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Phase 1: [Title]](#phase-1-title)
- [Phase 2: [Title]](#phase-2-title)
- [Rejected Splits](#rejected-splits)
- [File Inventory](#file-inventory)
- [Verification Summary](#verification-summary)

## Progress

<!-- Place this immediately after the TOC for visibility.
One checkbox per phase — intra-phase state is tracked by each phase's Verification
checklist, not duplicated here.
This section is authoritative when resuming work: update it at every phase and
sub-task completion.
Link each phase to its heading, using the same regenerated anchors as the TOC.
-->

- [ ] [Phase 1: [Title]](#phase-1-title)
- [ ] [Phase 2: [Title]](#phase-2-title)

* * *

## Scope

<!-- Dedicated section so it's scannable.
State what this plan covers and what it explicitly does not.
If a design doc exists, this section must agree with its Scope section; note any
deliberate divergence explicitly.
-->

This plan covers:

1. …
2. …

**Out of scope:**
[Anything deliberately excluded — including deployment, rollout, or migration
execution if this plan stops at merge — and where it is covered, if applicable.]

* * *

## Current State

<!-- Briefly describe the relevant parts of the system as they exist today.
This establishes the baseline so the reader understands what's changing and why.
Include key file paths or components involved.
Keep it factual — save opinions for design decisions.
-->

[What exists now, what's missing, key constraints discovered during research.]

* * *

## Desired End State

<!-- Describe what the system should look like when this plan is fully implemented.
This is the acceptance target — an implementer should be able to read this section and
know when they're done.
Include observable behaviors, not just internal structure.
Each phase also carries its own "Done when" line at phase granularity.
-->

[Description of the target state after all phases are complete, and how to verify it
was reached.]

* * *

## Assumptions and Gaps

<!-- Assumptions: things the design treats as given but doesn't state explicitly.
Gaps: line-level choices inside an already-scoped sub-task that the implementer will
make as they go.

Anything bigger than that — anything whose answer changes phase structure, the File
Inventory, or user-visible behavior — is an open question and must be resolved before
the plan is finalized (see SKILL.md's Workflow).
A decision deferred to a named checkpoint ("revisit after Phase 1's spike") may be
recorded here; an undated "TBD" may not.

Omit this section if the source material is fully explicit and there are no notable
unknowns.
-->

**Assumptions:**

- [Something the design depends on but doesn't state.
  Note where the implementer can confirm it.]

**Gaps:**

- [A line-level call the implementer will make — a corner case, error path,
  observability question. Note who decides if it isn't the implementer.]

* * *

## Prerequisites

<!-- Call out dependencies on other plans, prior work, or shared components that must
exist before this plan can start.
If a prerequisite might already be satisfied, say so ("if X already exists, Phase 1 can
be skipped").

Omit this section if there are no external prerequisites.
-->

- [Dependency description]. If already implemented, Phase 1 can be skipped.

* * *

## Architecture Overview

<!-- Provide the "big picture" before diving into phases.
This section answers "what are we building and why does it look this way?"
An implementer should be able to read this section alone and understand the overall
design. -->

### How it works

[High-level description of the feature's runtime behavior, numbered steps or a short
narrative.]

### Key design decisions

<!-- Ownership rule:
- Architectural decisions (components, approach, trade-offs) belong in the design doc.
  If one exists, link its Key Decisions section here — do not restate them.
- Record here only decisions made during planning that the design doc doesn't cover:
  phase structure, sequencing, and cross-phase choices.
- Decisions confined to a single phase's code go in that phase's Design Decisions
  subsection instead.
Each entry names what was chosen, the alternatives considered, and why this approach
wins. -->

- **[Decision].** [Rationale.]

### Component diagram

<!-- ASCII art or a brief textual description showing how the new components relate to
each other and to existing code.

Omit this subsection if the feature is simple enough that a diagram adds no value.
-->

```
[diagram]
```

* * *

## Phase 1: [Title]

<!-- A phase should be independently compilable and testable.
If it can't be verified on its own, redraw the boundary — usually by merging it with
the phase that consumes its output.

Repeat this phase structure (Depends on, Done when, numbered sub-tasks, Design
Decisions, Tests, Verification, Rollout, Implementation Notes) for every phase.
-->

[Brief description of this phase's goal and why it comes first.]

**Depends on:** [Nothing / Phase X (what it consumes). Say "can run in parallel with
Phase Y" when order between phases is arbitrary.]

**Done when:** [One to three lines of observable end state — the phase-level acceptance
target a PR reviewer can check the diff against.]

### 1.1 [Sub-task Title]

<!-- Label the file line "**File:**" for existing files, "**New file:**" for files that
don't exist yet.
These file lines are the source of truth for the File Inventory.
-->

**File:** `path/to/File.java`

[Description of what changes or what the new code does.
Include short code snippets only to show interface shape or critical seams — see "Code
in the plan" in SKILL.md.]

```java
// Short — interface signature, type definition, or the 5–15 line seam
// where new code attaches to existing code. NOT a full implementation.
// Reference existing patterns by pointer instead of duplicating source.
```

**Notes:**
- [Implementation details, edge cases, or constraints worth calling out.]

### 1.2 [Sub-task Title]

…

### Design Decisions

<!-- Non-obvious choices confined to this phase's code.
Each entry names the approach chosen, alternatives considered, and why this approach
wins. Cross-phase or architectural decisions belong in Key design decisions or the
design doc, not here.

Omit this subsection if the phase has no non-obvious design choices.
-->

**[Decision title]:** [Approach chosen].
[Alternatives considered and why they were rejected.]

### Tests

**File:** `path/to/TestFile.java`

<!-- List test cases by name with a short description of what each verifies.
For complex components (FSMs, handlers), use numbered sub-cases with explicit state
diagrams and assertion lists.
-->

Tests:
- [Test description — what scenario, what assertion.]
- [Test description.]

### Verification

#### Automated

- [ ] Standard gate for `[module]` — commands in
  [Verification Summary](#verification-summary)
- [ ] [Phase-specific check, if any — e.g., a migration dry-run or integration test
  outside the standard gate]

#### Manual

<!-- Omit this subsection if the phase can be fully verified by automated checks. -->

These checks require a human. An agent implementing this phase must stop and request
verification rather than checking these boxes.

- [ ] [Observable behavior to verify by hand.]

### Rollout

<!-- Only for phases that ship an operational change: a migration that runs against
live data, a feature flag, infra changes, or code that must deploy in a specific order
relative to other changes.
Cover: deploy ordering, flag state at ship time, the rollback story, and what to
monitor after shipping.

Omit this subsection if the phase ships entirely through the normal merge-and-deploy
path.
-->

- [Deploy ordering, flag state, rollback story, what to watch.]

### Implementation Notes

Filled in during implementation, not during planning. Record dated entries for
deviations from the plan, surprises, and newly discovered work. If an entry invalidates
a later phase or the File Inventory, update those sections too — the Notes are the
changelog; the plan body is the current truth.

<!-- Leave only the placeholder below in the initial plan.
Example entry:
- **2026-03-24:** Switched from subclass to composition for X because Y didn't expose
  the needed hook. Phase 3 will need to inject X differently — Phase 3's sub-tasks
  updated to match.
-->

*None yet.*

* * *

## Phase 2: [Title]

<!-- Same structure as Phase 1. Add further phases as needed. -->

…

* * *

## Rejected Splits

<!-- Phase decompositions that looked tempting but would have left the codebase worse
off — dead code, broken intermediate states, untestable partial work, or later phases
forced to redo earlier ones.
Documenting them here keeps the chosen split from being relitigated.
For a single-phase plan, note here why no split survived.

One or two sentences per rejected split.

Omit this section if no plausible alternative splits were considered.
-->

- **[Alternative split — e.g., "Split Phase 2 into 2a (data model) and 2b (handler
  wiring)"].**
  [Why it was rejected — e.g., "2a would have introduced an unused schema column with
  no consumer, leaving the migration in a half-applied state until 2b shipped."]

* * *

## File Inventory

<!-- A derived index of every file the plan touches.
The per-sub-task file lines in the phases are the source of truth; regenerate this
table from them whenever a phase changes, and reconcile it at each phase close.
Use full repository paths.
The Phase column plus the Progress section together answer "does this file exist
yet" for an implementer starting mid-plan.
-->

| File | Phase | Change | Purpose |
| --- | --- | --- | --- |
| `module/src/main/java/org/…/NewClass.java` | 1 | New | Brief purpose |
| `module/src/test/java/org/…/NewClassTest.java` | 1 | New | Unit tests for NewClass |
| `module/src/main/java/org/…/ExistingClass.java` | 2 | Modify | What changes |

* * *

## Verification Summary

<!-- This section is the single home of the gate commands.
Per-phase Verification checklists reference it and list only phase-specific extras.
Adapt the commands to the project's build system (see "Adapting to the project" in
SKILL.md); the commands below are a Maven example.
In a flat (single-module) repo, replace the matrix with one per-phase command list.
-->

Standard per-phase gate:

```bash
mvn -q spotless:apply
mvn -q -pl [module] clean compile
mvn -q -pl [module] test -Dtest=[TestClass]
```

The final phase additionally runs a full build:

```bash
mvn -q clean verify
```

| Phase | Build scope | Test target |
| --- | --- | --- |
| 1 | `[module]` | `[TestClass]` |
| 2 | `[module]` | `[TestClass]` |
| Final | full build | all tests (`mvn -q clean verify`) |
