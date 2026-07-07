---
name: writing-technical-design-documents
description: Write a standalone Markdown technical design document from a structured template (Problem, Constraints, Scope, Proposed Approach, Key Decisions, Risks). Use whenever the user asks to write, draft, or create a technical design document, design doc, technical design, RFC, tech spec, or architecture proposal — "write a design for X", "draft a design doc", "spec out how we'd build X" — or wants an approach evaluation captured as a written document before implementation. For documenting how an already-built system works, use writing-architecture-documents instead. For a phased, file-level execution plan of an already-decided approach, use writing-implementation-plan-documents instead.
---
# Writing Technical Design Documents

Follow the template in `references/technical-design-document-template.md` when writing
technical design documents.

Read the template before starting.
It contains HTML comments explaining the purpose of each section and how to fill it in.
These comments are guidance for you — do not include them in the output.
Replace every `[bracketed placeholder]` with real content: a finished document contains
no brackets and no HTML comments.

## Output

Write the design document as a single Markdown file.
Follow the repo's existing convention for design docs (`docs/design/`, `docs/rfcs/`,
`design/`, etc.); if none exists, use `docs/design/<feature-slug>.md`.

The user's requested format and the repo's existing conventions win over the template.
When asked for something lighter, keep Problem, Proposed Approach, and Key Decisions —
Key Decisions is never cut.
When editing an existing document, preserve its structure.

## Workflow

Get alignment before writing the full document.
Before drafting, present:

1. The problem statement, in two or three sentences
2. The candidate key decisions, with your leaning on each
3. Any open questions you can't answer from the code

Wait for the user's response before writing the full document.
If you're running non-interactively, or the user has said to proceed without review,
skip the round-trip and carry your unresolved assumptions into Risks and Open Questions
instead of silently deciding them.

## What a technical design document is (and isn't)

A technical design document captures the *what* and *why* of an approach — components,
responsibilities, interactions, key decisions, and trade-offs.
It sits between research ("what did we learn?") and an implementation plan ("what files
do we change, in what order?").

Write at the level of components and contracts, not individual files or lines of code.
An experienced developer should be able to read the document and understand how the
pieces fit together without needing to know exactly where each piece lives.

## Filling in the document

When writing a technical design document, you need real context about the codebase and
problem space. Before drafting:

- Read the relevant source code to understand the current state
- Identify existing components, interfaces, and patterns that the design interacts
  with
- If the user references research or requirements docs, read those too

Use what you learn to fill the template with specifics, not placeholders.
Current State claims must be verifiable: if you did not confirm a behavior in code or a
referenced document, either verify it or list it as an open question — never state
unverified behavior as fact.

If a research or requirements doc exists, link it and keep Current State brief.
If none exists, Current State must be self-contained: name the actual classes and
subsystems involved and describe their current behavior.

## Key Decisions section

This is the most valuable part of the document.
For each significant structural choice:

- Name what you chose and why
- List alternatives that were genuinely considered — an alternative counts only if you
  can say what would have to be true for you to switch to it
- Explain the rationale in terms of the constraints and goals specific to this project,
  citing constraints by name (C1, C2, …) rather than restating them

Most design documents have 2–5 key decisions.
Small features may have just one; large subsystem designs may have more than five.
Never invent a decision to hit a count — a decision belongs here only if reasonable
engineers could argue about it.
If you have many more than five, some are probably implementation details that belong
in the plan instead.

## Quality bar

A design document is ready when a reader could *disagree* with it — if no statement in
the document is falsifiable, it is too vague. Check before delivering:

- Every Rationale cites a constraint or goal stated elsewhere in the document; it never
  restates the decision in different words.
- Every component has a responsibility a reviewer could test a design change against,
  not a label like "handles the persistence logic".
- Current State contains only verified behavior.

Example — a bad vs. good Rationale:

> **Bad:** We chose the event-driven approach because it is more flexible and scalable.
>
> **Good:** We chose the event-driven approach because tag changes already flow through
> the gateway event bus (see Current State), and a polling design would introduce a
> second scheduling subsystem to configure and maintain (violates C2).

## Sections to omit when not applicable

- **Constraints** — omit if there are no external constraints worth calling out
- **Interface / Protocol / API Changes** — omit if the feature has no externally
  visible surface changes
- **Failure Modes and Degraded Operation** — omit only if the design has no runtime
  surface
- **Performance and Capacity** — omit if load, scale, and resource cost genuinely don't
  bear on the design
- **Migration and Compatibility** — omit for greenfield work with no upgrade path or
  existing data to carry forward
- **Future work** — omit if there's nothing to call out

**Security Considerations** is never omitted: if there is no new attack surface, say so
and why in a sentence.
