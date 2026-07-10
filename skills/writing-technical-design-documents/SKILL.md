---
name: writing-technical-design-documents
description: Write a standalone Markdown technical design document from a structured template (Problem, Goals, Constraints, Scope, Proposed Approach, Key Decisions, Assumptions, and Risks). Use whenever the user asks to write, draft, or create a technical design document, design doc, technical design, RFC, tech spec, or architecture proposal — "write a design for X", "draft a design doc", "spec out how we'd build X" — or wants an approach evaluation captured as a written document before implementation. Do not use for documenting only how an existing system works. For a phased, file-level execution plan of an already-decided approach, use writing-implementation-plan-documents instead.
---
# Writing Technical Design Documents

Read and follow `references/technical-design-document-template.md` before writing.
Apply its HTML guidance comments without copying them into the output. Replace every
bracketed template placeholder; a finished document contains no template placeholders
or guidance comments.

## Outcome and boundaries

Write the design document as a single Markdown file.
Follow the repo's existing convention for design docs (`docs/design/`, `docs/rfcs/`,
`design/`, etc.); if none exists, use `docs/design/<feature-slug>.md`.

The user's requested format and the repo's existing conventions win over the template.
When asked for something lighter, keep Problem (including Goals and Success Criteria),
Proposed Approach, Key Decisions, and any material assumptions, risks, or open questions.
Key Decisions is never cut.
When editing an existing document, preserve its structure.

A technical design document captures the *what* and *why* of an approach — components,
responsibilities, interactions, key decisions, and trade-offs.
It sits between research ("what did we learn?") and an implementation plan ("what files
do we change, in what order?").

Write at the level of components and contracts, not individual files or lines of code.
Do not implement the proposed design unless the user separately asks for implementation.

## Workflow

Inspect the relevant code, documents, and repository conventions, then write the full
design without a pre-draft approval round-trip unless a missing decision would materially
change scope, public behavior, compatibility, security, or architecture and cannot be
resolved from available evidence.

When blocked, ask the smallest focused question. Otherwise proceed and record material
assumptions explicitly in Assumptions, Risks, and Open Questions. Do not silently decide
an issue that could invalidate a Key Decision.

Stop investigating when the available evidence supports the current state, constraints,
public contracts, and proposed decisions. Do not keep searching only to add optional
background or polish.

## Grounding

Verify every claim that materially drives a decision, including current behavior,
external requirements, API contracts, compatibility guarantees, performance budgets,
and security constraints. Link or name the supporting source. Label inference and
unknowns instead of presenting them as facts. Do not invent project details, metrics,
dates, owners, or roadmap status.

If a research or requirements document exists, link it and keep Current State brief.
Otherwise make Current State self-contained: name the actual classes and subsystems and
describe only behavior verified in code or another cited source.

## Key Decisions section

For each significant structural choice:

- Name what you chose and why
- List alternatives that were genuinely considered — an alternative counts only if you
  can say what would have to be true for you to switch to it
- Explain the rationale in terms of the constraints and goals specific to this project,
  citing them by name (G1, C1, …) rather than restating them

Most design documents have 2–5 key decisions.
Small features may have just one; large subsystem designs may have more than five.
Never invent a decision to hit a count — a decision belongs here only if reasonable
engineers could argue about it.

## Completion criteria

A design document is complete when:

- It is saved at the requested or conventional location as one Markdown file.
- It contains no template placeholders or guidance comments.
- Every load-bearing claim is grounded in a verified source or labeled as an assumption,
  risk, inference, or open question.
- Every Rationale cites a named constraint or goal and does not merely restate the
  decision.
- Every component has a responsibility a reviewer could test a design change against,
  not a label like "handles the persistence logic".
- Every material decision names the chosen approach, genuine alternatives, rationale,
  and consequences.
- Optional sections are either substantively completed or omitted as directed by the
  template; Security Considerations is always present.
- The design stays at the component-and-contract layer and does not drift into an
  implementation plan or implementation changes.

A reader must be able to disagree with the document: if no claim is falsifiable, the
design is too vague.

Example — a bad vs. good Rationale:

> **Bad:** We chose the event-driven approach because it is more flexible and scalable.
>
> **Good:** We chose the event-driven approach because tag changes already flow through
> the gateway event bus (see Current State), and a polling design would introduce a
> second scheduling subsystem to configure and maintain (violates C2).
