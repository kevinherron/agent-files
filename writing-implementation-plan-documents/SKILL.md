---
name: writing-implementation-plan-documents
description: Write a standalone Markdown implementation plan — a phased, file-level breakdown of how to build an already-decided feature or change. Use whenever the user asks to write, draft, or create an implementation plan, technical plan, engineering plan, feature plan, or migration plan, says "plan out the implementation", "break this into phases", "break down this ticket", "write up how we'd build this", or wants to turn a design doc, research doc, or spec into a phased execution plan. For deciding and justifying the approach itself (components, trade-offs, key decisions), use writing-technical-design-documents first. Do not use for project or sprint scheduling, or when the user wants a quick verbal plan rather than a plan document.
---
# Writing Implementation Plans

Follow the template in `references/implementation-plan-template.md`.
Its HTML comments explain the purpose of each section and how to fill it in — apply
them, but never emit them.
Replace every `[bracketed placeholder]` with real content: a finished plan contains no
brackets and no HTML comments.
If unsure of the target shape or quality, read `references/example-plan-excerpt.md`, a
filled-in excerpt of one phase.

All template sections are required except those whose comment says "Omit this section
if…" — omit those when the stated condition holds, and remove the corresponding Table
of Contents entry when you do.

## Output

Write the plan as a single Markdown file.
Follow the repo's existing convention for plans (`docs/plans/`, `plans/`,
`docs/implementation/`, etc.); if none exists, use `docs/plans/<feature-slug>.md`.
The user's requested location wins over both.

## Right-sizing

- If the work is roughly one phase touching a handful of files, say so and offer to
  implement it directly (or write a short task list) instead of producing a plan.
  If the user still wants a plan, collapse it: skip the TOC, Progress, Architecture
  Overview, and File Inventory — a one-phase plan is Scope, Current State, Desired End
  State, the phase body, and its verification.
- One phase is a valid answer for full-size plans too.
  If there is no natural seam, do not manufacture one — write a single phase and note
  in Rejected Splits why no split survived.
- If the plan would exceed roughly 6–8 phases or crosses independent workstreams, stop
  and split it into multiple plans, each listing the others it depends on under
  Prerequisites.

## Workflow

Work back and forth with the user — start with open questions and an outline, and get
alignment before writing the full plan.
If you're running non-interactively, or the user has said to proceed without review,
skip the round-trip and record unresolved items in Assumptions and Gaps as explicitly
unconfirmed assumptions instead of silently deciding them.

**No open questions in the final plan.** The finished plan must be complete and
actionable — every decision made, no TBDs.
(The one exception is each phase's Implementation Notes placeholder, which is
deliberately left empty until implementation.)

Use this rule to decide what counts as an open question versus a gap:

- If the answer changes phase structure, the File Inventory, or user-visible behavior,
  it is an open question — stop and resolve it with the user.
- If it only changes a line-level choice inside an already-scoped sub-task, record it
  as a Gap for the implementer.
- If only the codebase can answer it, investigate before writing the plan — or produce
  a research doc first (see the `writing-research-documents` skill).
- If only doing early-phase work can answer it, make Phase 1 a spike with a concrete
  deliverable, plan the dependent phases at outline fidelity, and mark each with
  "Checkpoint: revisit after Phase 1."
  A scheduled decision with a named trigger is not a TBD.

## Phase quality

Phases need to hold up as discrete, shippable units — the boundaries matter as much as
the contents.

- Size each phase for one focused coding session — roughly one PR: typically two to
  five sub-tasks, a diff a reviewer can read in about 30 minutes. If a phase pushes
  that bound, say so explicitly in the plan: either split it or justify why splitting
  would leave the codebase worse off than the size.
- Every phase leaves the codebase compiling and its tests passing.
  No intentionally broken intermediate states or mid-refactor checkpoints.
- A phase must not require later phases to retroactively patch up its work.
  If Phase 2 has to redo something Phase 1 did, the boundary is wrong.
  Planned removal of deliberately temporary scaffolding — compatibility layers, feature
  flags, migration shims — by a later phase is not patch-up; unplanned rework is.
- Prefer boundaries on natural seams: module ownership, API contracts, data model
  changes, backend/frontend separation, compatibility layers, migration paths, or
  independently testable behavior.
  Don't split on arbitrary file counts or vague "setup" work.
- If a tempting split would leave dead code, broken behavior, or untestable partial
  work, reject it and capture the reasoning in the plan's "Rejected Splits" section so
  the choice isn't relitigated.

## Code in the plan

A plan communicates *decisions* and *shape*, not implementations.
The implementation session is where code actually gets written — if the plan pre-writes
it, the session becomes a copy-paste exercise and the implementer has nothing to think
about.

Show code only when it communicates one of:
- A new type / interface / record / enum shape (signatures, field lists).
- A critical seam where new code attaches to existing code.
- A genuinely novel pattern that doesn't exist elsewhere in the codebase.

Don't show code for full method bodies, boilerplate, or mirrors of patterns that already
exist in the codebase.
Reference patterns by pointer ("mirror `McpConfigLoader`") instead of duplicating
source.

Keep snippets short — roughly 10–15 lines per block.
If a snippet exceeds that, cut it to the signature or seam, or replace it with a
pointer to the pattern it mirrors.

Detailed codebase grounding — quoted source from existing files, API surfaces, file
snapshots — belongs in a separate per-phase grounding document produced in a follow-up
session (via the `writing-phase-context-docs` skill, if available), not inline in the
plan.

## Adapting to the project

The template uses Java and Maven in its placeholder examples, but the structure is
language-agnostic. Replace all language-specific references — file extensions, build
commands, test frameworks, directory layouts — with whatever the project actually uses.
For example, a Python project should reference `.py` files, `pytest`, and
`pyproject.toml`; a TypeScript project should use `.ts`, `vitest` or `jest`, and
`package.json`.

Adapt the topology too, not just the language.
The Verification Summary's per-module gate assumes a multi-module build: in a flat
repo, replace the matrix with a single per-phase command list; in a monorepo,
substitute the workspace or package unit for "module."

## During implementation

The plan is a living document. One rule governs updates: **Implementation Notes are the
changelog; the plan body is the current truth.**

- Record deviations, surprises, and newly discovered work in the current phase's
  Implementation Notes, dated.
- When a deviation invalidates a later phase's steps or the File Inventory, edit those
  sections to match reality and record why in the Notes — never leave a phase body you
  know is wrong.
- At each phase and sub-task completion, update the Progress section and the phase's
  Verification checklist. Progress is authoritative when resuming.
- Manual verification items require a human: stop and request verification rather than
  checking those boxes yourself.

A resuming implementer reads, in order: Progress, Architecture Overview, all prior
phases' Implementation Notes, their own phase, and the Verification Summary (for the
gate commands).
