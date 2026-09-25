# Writing issues

Read this before creating or rewriting issue descriptions. The reader should be able
to understand the work and decide what needs review without reconstructing its history.

## Write the current brief

Use only the sections the issue needs. A useful shape is:

- Problem and result: what happens today, who it affects, and what should happen.
- Scope and acceptance: a few observable outcomes or concrete review points.
- Current state: what is delivered, what remains, and any blocker or decision needed.
- Evidence: a short relevant result, material limitations, and links for deeper review.

Keep acceptance criteria specific enough to judge completion. Do not replace them
with "see the plan" or hide a failing requirement in an agent handoff. Explain
review state precisely; implemented, tested, merged and released mean different things.
Avoid repeating fields already visible in Linear unless that distinction needs explaining.

Prefer "Generated code compiles against the published library" to "The downstream
consumer compatibility gate is satisfied." Name the actor, behavior and consequence.
Keep technical identifiers when the reader needs them, but explain their role. Use
short paragraphs and bullets instead of stacked qualifiers or dense status tables.

## Use the smallest helpful view

Borrow show-me's approach: choose the smallest view that explains the point and place
it beside a short explanation. These choices are self-contained; invoking another
skill is not required for routine issue writing.

| What needs explaining | Useful view |
| --- | --- |
| Changed behavior | One before/after example or short diff |
| A rule or algorithm | A few lines of pseudocode |
| Ownership or execution order | A shallow file tree or call tree |
| Interaction between components | A small Mermaid diagram |
| Distinctions or options | A compact comparison table |

For example, an issue about duplicate output files could use:

```diff
- Two types named Status silently overwrite the same Status.java file.
+ Generation reports the conflicting types before writing output.
```

Then give the acceptance points: the error identifies both types, generation leaves
existing output untouched, and unique names still generate successfully. A short
example often does more work than several abstract paragraphs. Use the whole block
when omitted context would hide ownership or order. Skip a visual when plain prose
is clearer; do not add a separate HTML artifact to a routine issue just for decoration.

## Maintain and shorten

At a checkpoint, replace the affected current-state text. Add only evidence relevant
to this issue's criteria. Link shared verification once instead of copying the same
project checkpoint into every issue. Comments can record a decision or review reply;
they should not become an alternative agent activity log.

When an existing issue has grown into a history log, preserve meaningful decisions,
evidence and provenance in a separate historical record before removing them. If the
old text is the only complete record, a frozen copy is appropriate. Verify the saved
record, link it, then rewrite the current description. Label the archive's audience
and historical status so its obsolete blockers cannot be mistaken for current work.
Reuse a suitable record rather than creating one document per edit. See
[Working documents](working-documents.md) for handoff and ledger responsibilities.

Do not move the same bulk into the plan, index or What's next. Each current document
should retain its own purpose; detailed history belongs in the historical record.

## Check before saving

Read the description as a reviewer who has not followed the conversation:

- Can I explain the problem, intended result and acceptance criteria in one read?
- Is it clear what remains or what decision is needed?
- Are terms concrete and understandable, with a small example where useful?
- Is it within the skill's length guidance, without hiding scope or limitations?
- Are repeated history and recovery details in clearly labeled, linked records?

After saving, read back the issue and check that the brief, links and any visual
survived the edit. Confirm that shortening did not change scope or completion status.
