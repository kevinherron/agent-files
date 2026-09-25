# Working documents

Read this when setting up the project's document system, migrating material, or
updating a plan, research record or handoff.

## Canonical records

Use these defaults unless the project has an explicit convention:

| Material | Intended audience | Home and lifecycle |
| --- | --- | --- |
| Work status | Human reviewers and decision makers | Issue with current scope, acceptance criteria, blockers and concise evidence links |
| Working docs index | Anyone entering the project | Short project document with canonical links and document roles |
| What's next | People selecting work and coordinating agents | Live project document for ranked actions and readiness |
| Research | People evaluating findings and implementers | Dated document with source revisions, evidence and conclusions |
| Design or implementation plan | Design reviewers and implementers | Project or issue document; update the active draft in place |
| Agent handoff | Agent or engineer resuming execution | Current recovery instructions, exact baselines, open decisions and verification limits |
| Change and evidence ledger | Maintainers investigating history | Historical entries for material changes, decisions and verification evidence |
| Product documentation | Library users and contributors | Repository files reviewed and committed with the software |
| Scratch and raw output | Investigators needing raw detail | Temporary files or artifact storage; preserve essential conclusions remotely |

State the intended audience and purpose near the top of supporting documents,
especially handoffs and ledgers. For example, "Audience: agents and engineers resuming
implementation. This document contains recovery details; human review starts in the
linked issues." Record status, owner, issue links and source baseline when they affect
interpretation. Draft, accepted, historical and superseded are document conventions,
not assumed native Linear fields. Do not label a plan accepted merely because it has
been migrated or promoted from a reference snapshot to an active draft.

The index should identify which documents can change and which preserve history.
Link superseding records in both directions. Keep current plans and indexes updated
in place, with history linked separately. In a frozen historical handoff, old next
steps can remain with a pointer explaining that the live queue governs new work.

## Migration

1. Inventory the supplied local sources and existing project documents. Retrieve
   full remote bodies and compare them before deciding to reuse, update or create.
   Preserve addenda and newer remote decisions, even when absent from the local file.
2. Establish each document's role. Research can remain a historical snapshot while
   a plan becomes the active working draft. Preserve original baselines, unresolved
   decisions and submission restrictions. Choose one canonical editable copy.
3. Preserve content and useful provenance. For substantial migrations, record the
   source filename, source revision or content hash, and migration date. Distinguish
   a copied observation from a newly verified fact. Do not turn historical issue or
   release status into a claim about the current state.
4. Replace local-only navigation with canonical links where possible. Keep original
   paths as provenance when useful. Save remotely, retain returned IDs/URLs, then
   verify the content, examples, tables and links by reading it back. Markdown
   normalization alone is not data loss, but changed destinations or code are errors.
5. Update the index and project overview to point at the canonical records. Add
   backlinks where they help navigation. Correct stale overview summaries with dated
   evidence while preserving relevant historical context.
6. Preserve original files unless removal was requested. Mark their role using a
   local pointer or source note, avoiding unrelated edits. When the user wants working
   documents kept out of product commits, inspect tracking first: existing tracked
   files need a deliberate migration decision. For untracked copies, narrow local
   excludes can protect the selected files and scratch directory. Do not ignore all
   of docs/ or change shared ignore policy merely to hide working copies.

Local copies are caches or preserved sources. Refresh before editing and publish
changes deliberately. Do not establish competing editable copies or claim automatic
two-way synchronization. A shared index is the bootstrap for another machine; a
local pointer alone is insufficient.

## Handoffs and history

A handoff should let another worker identify the exact deliverables, resume point,
remaining decisions and verification limits without reading the original conversation.
Include issue-to-PR/commit mappings and ownership when they matter to recovery.
Link the live queue rather than maintaining a second current priority list.

Reuse a current handoff for the workstream and replace obsolete recovery instructions.
Create a frozen milestone snapshot only when retaining that state is useful. A ledger
can preserve material changes with the date, affected issues, decision or outcome,
evidence and relevant limits. Append meaningful entries, not every command or repeated
status check. It records history; it does not own current status or priorities.

Keep detailed evidence in these supporting records: exact source/runtime/corpus
identities, checks performed, results, known failures, unresolved findings and
acceptance gaps. Prefer immutable source links for versioned expectations. Preserve
the difference between a successful gate and cases deliberately recorded as failures.
Surface any limitation affecting acceptance in the issue's short summary too.

Create only the records needed. A handoff may link a ledger's evidence rather than
copy it, or one supporting document may have clearly separate current handoff and
historical sections. Neither belongs inside the human-facing issue. Preserve enough
context in the issue that reading these operational records is optional for review.

Large raw logs and generated trees may remain in CI or separate artifact storage.
State their location, retention limits and whether they were actually uploaded.
Do not describe a local .git/ archive as portable storage or assume CI retention is
permanent. Before workspace cleanup, identify unique evidence needing a shared copy.
Document migration alone does not authorize uploading every raw artifact or deleting
the originals.
