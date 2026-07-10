---
name: writing-implementation-plan-documents
description: Write a standalone Markdown implementation plan or coordinated plan set for an already-decided feature or change, with readiness state, code grounding, capability-based work packages, file-level changes, acceptance criteria, verification, and downstream handoffs. Use whenever the user asks to write, draft, or create an implementation plan, technical plan, engineering plan, feature plan, migration plan, phased execution plan, or breakdown of how to build a design, research result, specification, or ticket. For deciding and justifying the architecture itself, use writing-technical-design-documents first. Do not use for project scheduling or quick verbal plans.
---

# Writing Implementation Plans

Follow `references/implementation-plan-template.md`. Apply its HTML comments, but never
emit them. Replace every bracketed placeholder. Read
`references/example-plan-excerpt.md` only when calibration is useful.
Keep every template section unless its comment explicitly permits omission, and remove
omitted sections from the Table of Contents.

Use the plan as the technical execution contract. Keep worker assignment, retries,
parallelism, progress commentary, and recovery policy in `$goal-orchestration`; keep the
goal's deliverables and terminal conditions in `$goal-prompting`.

## Output

Write one Markdown plan using the repository's existing convention. If none exists,
use `docs/plans/<feature-slug>.md`; the user's path wins.

When the work must split across independent or dependency-ordered plans, write a lean
plan-set manifest plus the focused plans only when the user authorizes multiple files.
The manifest records stable stage and plan IDs, paths, readiness, prerequisites, shared
invariants, required handoff fields, and the final gate. Do not embed `/goal` blocks,
worker assignments, or generic orchestration instructions in it.

## Readiness And Grounding

Every full plan declares:

- `Plan ID`: stable within its plan set.
- `Status`: `Draft`, `Conditional`, or `Ready`.
- `Parent manifest`: path or `None`.
- `Grounded against`: branch, commit, handoff, artifact version, or inspection date.
- `Re-ground before`: a named work package or `None`.

Use these statuses consistently:

- `Ready`: implementation can begin; no blocking decision remains, and existing seams
  plus intended new artifacts are grounded at file level.
- `Conditional`: the target is decided, but later implementation depends on an earlier
  handoff or code state. Record the re-grounding trigger and keep affected work packages
  at outline fidelity until it is satisfied.
- `Draft`: a material decision remains unresolved. Do not present the plan as safe for
  unattended implementation.

For `Ready` plans, name exact existing files and intended new file paths. For
`Conditional` plans, still name every existing attachment seam exactly; use
`Destination` only for not-yet-created artifacts whose exact path depends on the named
handoff. Before the affected work package starts, inspect actual code, replace each
destination with `File` or `New file`, update the inventory, and promote readiness.

Do not invent precise paths to make a dependency-deferred plan look ready.

## Workflow

1. Inspect the source design, research, specification, issue, relevant code, tests,
   repository instructions, and prior handoffs before outlining work.
2. Identify scope, observable end state, material decisions, state or data flow,
   failure behavior, security or privacy concerns, files or destinations, and
   verification surfaces.
3. Ask the user only when a missing answer materially changes behavior, scope, work
   package boundaries, external side effects, or authorization. Otherwise investigate
   or record a bounded assumption.
4. Choose readiness honestly. A non-interactive run may produce a `Conditional` or
   `Draft` plan with owned, scheduled open decisions; it must not silently decide them
   or label the plan `Ready`.
5. Write the plan, then run the bundled
   `<skill-directory>/scripts/validate_implementation_plan.py <plan>` and fix every
   reported error before delivery.

No final plan may contain an unowned or unscheduled open decision. For each retained
open decision, record the owner or authoritative source, resolution trigger, affected
work packages, and behavior if unresolved.

Treat choices affecting public APIs, protocol status, persistence, migrations, timing,
retry or drop policy, authorization, compatibility, or user-visible behavior as
material decisions—not implementer gaps.

If only code inspection can answer a question, inspect it or produce research first.
If only early implementation can answer it, make the first work package a spike with a
concrete artifact and verification, mark dependent work packages `Checkpoint: re-ground
after WPx`, and keep the plan `Conditional` until that checkpoint is resolved.

## Right-Sizing And Plan Sets

- For work touching only a handful of files with one natural acceptance boundary, offer
  direct implementation or a short task list. If the user still wants a plan, collapse
  the template as described in its comments.
- One work package is valid. Do not manufacture phases.
- Split work at independently verifiable capabilities, API or module seams, migration
  states, compatibility boundaries, or rollout boundaries. Session length, PR size,
  subtask count, and reviewer time are secondary checks, not boundary generators.
- Do not create a work package solely for routine tests, documentation, or handoff
  updates when those belong with the behavior they validate. A separate test work
  package is justified only for a substantial independent harness or compatibility
  artifact.
- If a plan would exceed roughly six to eight work packages or crosses independent
  workstreams, split it into focused plans and add a manifest. Use `Stage` for manifest
  ordering, `Plan ID` for documents, `WP1`/`WP2` for local work packages, and numbered
  subtasks beneath them; do not reuse `Phase 1` at every hierarchy level.

## Context Economy

Describe the destination and important constraints rather than prescribing every coding
step. Include requirements, exact seams, state transitions or data flow, failure
behavior, tests, and validation. Leave ordinary implementation choices to the
implementer.

When an accepted design exists, link its authoritative sections instead of restating
architecture or trade-offs. Keep only the implementation-specific flow, attachment
points, sequencing decisions, and deviations. Put plan-set-wide invariants in the
manifest and repeat only high-risk local constraints in each plan.

Use code snippets only for a new type shape, a critical attachment seam, or a genuinely
novel pattern. Keep snippets to roughly 10–15 lines. Point to existing patterns instead
of copying them. Put large source snapshots or exhaustive grounding in a separate
artifact only when they are necessary for a later bounded work package.

## Work Package Quality

Each work package must:

- Have a stable ID, explicit dependencies, and an observable `Done when` contract.
- Leave the repository in a coherent, compilable, testable state.
- Deliver a capability or verified state rather than unused scaffolding.
- Name concrete files or permitted dependency-deferred destinations.
- Include success, failure, cleanup, cancellation, and security or privacy behavior when
  relevant.
- Put tests beside the behavior they validate and identify the required evidence.
- Avoid requiring a later package to redo earlier work. Planned removal of an explicit
  compatibility layer, flag, or migration shim is allowed.

Prefer natural seams over arbitrary file counts. Record plausible rejected splits when
they would have created dead code, broken behavior, untestable partial work, or repeated
verification without a meaningful capability boundary.

## Verification

Keep shared commands in one Verification Summary. Work packages reference that gate and
list only delta-specific checks.

- Prefer targeted tests, type or lint checks, affected-package builds, and a minimal
  smoke test while iterating; reserve the complete repository gate for defined plan or
  manifest boundaries.
- Prefer non-mutating verification. Treat formatter `apply` commands as preparation,
  not evidence, unless repository policy explicitly requires them as part of the gate.
- Do not prescribe repeated unchanged full builds.
- Use `Manual` only for genuinely human-only, subjective, physical-device, production,
  or externally authorized checks. Dependency direction, forbidden imports, formatting,
  generated files, and code invariants belong in automation or agent review.
- If verification cannot run, record why, the next-best check, and whether that prevents
  the plan or work package from being accepted.

## During Implementation

The plan body is current truth; Implementation Notes are the dated changelog.

- Update work-package-level Progress, the active work package's verification checklist, and
  notes after meaningful completion or deviation. Do not duplicate subtask progress in
  the top-level checklist.
- If a discovery invalidates a later work package, file inventory, readiness state, or
  open decision, update the plan immediately and record why.
- Stop for manual verification only when the item is genuinely human-only and blocks the
  next dependency. Otherwise preserve it as pending without halting safe independent
  work.

When another plan consumes this one, maintain a concise Downstream Handoff containing:

- Final public contracts and exact paths.
- Design deviations and rationale.
- Verification evidence.
- Required downstream configuration or re-grounding actions.
- Retained risks and unsupported behavior.

Do not use the handoff to narrate the entire implementation. Link code and dated notes
for detail.

A resuming implementer reads, in order: readiness metadata, Open Decisions, Progress,
relevant prior Implementation Notes or handoffs, the active work package, File
Inventory, and Verification Summary.
