# [Feature Name]: Technical Design

<!-- One to two sentence summary of the problem being solved and the proposed approach.
If a research doc, specification, or requirement motivates this design, name and link
it as part of the summary (e.g., "…, as proposed in [research doc]").
Never cite a document that does not exist.
-->

[One to two sentence summary of the problem being solved and the proposed approach.]

## Problem

### Current State

<!-- What exists today, and what's missing or broken.
If a research doc has the full context, link it and keep this brief.
If none exists, this section must be self-contained: name the actual classes and
subsystems involved and describe their current behavior.
Only state behavior verified in code or in a referenced document.
-->

[What exists today, and what's missing or broken.]

### Motivation

[Why this work matters.
Business reason, spec compliance, user need, etc.]

## Constraints

<!-- External forces that bound the solution space.
Label each constraint (C1, C2, …) so Key Decisions can cite it by name instead of
restating it.
Remove this section if there are no constraints worth calling out.

Examples: spec requirements, backwards compatibility, performance budgets, security
requirements, dependencies on other work in progress.
-->

- **C1** — [Constraint and its source.]

## Scope

<!-- Placed before the approach so reviewers know the boundaries before evaluating the
design. When an implementation plan exists, its scope section should agree with this
one.

If validating this design requires building infrastructure (simulators, test harnesses,
parity checks), list it as in-scope work — it has real cost.
-->

This design covers:

1. [Covered work.]

**Out of scope:**

<!-- Things a reviewer might assume are included and must be told are not.
Say where excluded work is tracked, if applicable.
-->

- [What's excluded, and where it's tracked if applicable.]

### Future work

<!-- Follow-on work this design deliberately enables but that is not part of this
effort. Helps reviewers distinguish deferred from forgotten.
Remove this subsection if there's nothing to call out.
-->

- [What could be built on top of this work later.]

## Proposed Approach

<!-- The core of the document.
Describe the approach at the level of components, responsibilities, and interactions —
not individual files or lines of code.
The implementation plan handles that detail.

An experienced developer should be able to read this section and understand *what* we're
building and *how the pieces fit together*, without needing to know exactly which file
each piece lives in.
-->

### Overview

<!-- High-level narrative of how the proposed solution works.
Tell the end-to-end story: what triggers the flow, which components it passes through,
and who owns what state along the way.
A few paragraphs or a numbered sequence — whatever communicates the flow best.
Don't make the reader assemble the system story from isolated component descriptions.
-->

[High-level narrative of how the proposed solution works.]

### Component Design

<!-- What components are new, what existing components change, and how they relate to
each other. This is the structural sketch that the implementation plan will refine into
file-level detail.

Include a diagram (ASCII, Mermaid, or textual) when it clarifies structure or
interaction; leave it out when it wouldn't.

For runtime subsystems, include the diagnostics/observability surface: what operators
see when this is healthy, degraded, or failed.
-->

[Prose describing the components, their responsibilities, and how they interact.
Focus on boundaries and contracts, not internals.
Each responsibility should be concrete enough that a reviewer could test a design
change against it.]

### Interface / Protocol / API Changes

<!-- New or changed surfaces that other code (or external systems) will depend on: wire
formats, public APIs, configuration knobs, data model changes, etc.

Signatures are contracts, not implementation detail — sketch new public signatures and
a short example call site rather than describing them in prose; reviewers can't judge
compatibility and usability from paragraphs.
State whether each change is breaking or non-breaking; if breaking, give the migration
path. Note versioning, deprecation, and stability expectations for new public surface.

Remove this subsection if the feature has no externally visible surface changes.
-->

[Description of changes, with signatures and example usage where a public surface is
involved.]

### Failure Modes and Degraded Operation

<!-- Failure semantics are part of the contract.
For each external dependency and each component boundary: what can fail, and what the
designed behavior is (retry, buffer, shed load, block, surface an error).
A design that only describes the happy path can't be reviewed.

Remove this subsection only if the design has no runtime surface.
-->

[What can fail, and how the design behaves when it does.]

### Security Considerations

<!-- New attack surfaces, trust boundaries crossed, authn/authz model, handling of
untrusted input, secrets or sensitive data.

Do not remove this subsection: if there is no new attack surface, say so and why in a
sentence. For designs that warrant a full analysis, use the threat-modeling skill.
-->

[Security impact of the design, or why there is none.]

### Performance and Capacity

<!-- Expected load and scale, back-of-envelope analysis for the hot path, and which
design choices exist because of it.
Stating a budget in Constraints is not the same as showing the design meets it.

Remove this subsection if load, scale, and resource cost genuinely don't bear on the
design.
-->

[Expected load, hot-path analysis, and the design choices it drives.]

## Migration and Compatibility

<!-- How we get from the current state to the proposed one: coexistence vs. replacement
of the old implementation, upgrade path for existing deployments and data, compatibility
guarantees kept or broken, rollback story.
For refactors this section often carries the most weight — the migration strategy can
decide the architecture.

Remove this section for greenfield work with no upgrade path or existing data to carry
forward.
-->

[Migration strategy, compatibility guarantees, and rollback story.]

## Key Decisions

<!-- The structural choices that constrain the implementation.
Each entry names the approach chosen, the alternatives genuinely considered, and why
this approach wins. Cite constraints by name (C1, C2, …) rather than restating them.

These decisions are *proposals* — they may change during implementation.
When they do, update this section or note the deviation in the implementation plan's
Implementation Notes (see the writing-implementation-plan-documents skill).
-->

### [Decision title]

**Chosen approach:** [What we're doing.]

**Alternatives considered:**

- **[Alternative A]** — [Why it was rejected, and what would have to be true for it to
  win.]
- **[Alternative B]** — [Why it was rejected, and what would have to be true for it to
  win.]

**Rationale:**
[Why the chosen approach is the best fit, citing the constraints and goals stated
elsewhere in this document — never a restatement of the decision. Include relative
cost/effort and dependency burden where they drove the choice.]

**Consequences:** [What this choice commits us to or makes harder later.
Omit if there's nothing worth noting.]

<!-- Repeat this subsection for each key decision.
Most design documents have 2–5 decisions; small features may have one, large designs more.
Never invent a decision to hit a count.
-->

## Risks and Open Questions

<!-- Things that could change the approach once implementation begins.

- **Risk**: a known unknown — something that *might* happen and would force a change in
  approach.
- **Question**: something that needs an answer before or during implementation —
  including assumptions you made without user review.

List every unknown that could invalidate a Key Decision.
If there are truly none, write "None identified" — never invent items to look complete.
As items resolve, mark them Resolved (with the answer, or a pointer to the Key Decision
that absorbed it) rather than deleting them, so review history survives.
-->

**R1 (Risk)** — [What might happen.]
**Impact:** [What changes in the approach if it does.]
**Status:** Open

**Q1 (Question)** — [What needs an answer, and by when.]
**Why it matters:** [What depends on the answer.]
**Status:** Open

## References

<!-- Pointers to related material.
Only real, verified links and paths — remove entries that don't apply, or the whole
section if empty.
-->

- [Motivating research or requirements doc, if any]
- [Specification, section reference, or external link]
- [Related prior art, similar implementations, or existing patterns]
