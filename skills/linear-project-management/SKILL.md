---
name: linear-project-management
description: Keep Linear issues readable, organize project documents, and maintain an evidence-backed What's next queue. Use for issue cleanup, project setup, document migration, prioritization, handoffs, and coordination checkpoints during Linear-backed work. Skip standalone issue lookups.
---

# Linear project management

Make it easy for a person to understand and review the work, and for another worker
to resume it from current evidence. Use Linear as the canonical home for working
research, plans and handoffs when establishing this convention or when the project
already follows it. Honor an explicitly chosen alternative storage system.

## Keep issues readable

Issue descriptions are current briefs for human review. Aim for 150–300 words;
simple issues can be much shorter. Above 400 words, edit down or move supporting
detail into a linked document. Keep a longer description only when the extra detail
is needed to understand the scope or acceptance criteria. Do not remove requirements,
unresolved decisions or material limitations just to meet a word count.

Explain the problem, intended result, acceptance or review points, and current blocker
or decision when relevant. Use plain words and concrete examples. Explain necessary
technical terms through the behavior they describe. Read
[Writing issues](references/writing-issues.md) before creating or rewriting descriptions.

Update the current brief in place. Remove resolved blockers and obsolete instructions;
do not accumulate dated checkpoints, agent handoffs or project-wide verification
dumps in the description or comments. Keep detailed recovery instructions and history
in separate documents labeled with their intended audience. Link them from a short
evidence summary. The issue must make sense without opening those records.

## Start from the project

Resolve the intended project and team from the request or existing context. Inspect
the project overview, documents and relevant issues before creating anything. Ask
only if the project cannot be identified reliably. Reuse existing document IDs and
links; do not create another index or plan because its title differs slightly.

Discover the available Linear tools and their current schemas. Project resources
provide an entry point; search supplements them. List/search results may truncate
document and issue bodies, so retrieve full content before editing or relying on
acceptance criteria. Follow pagination when claiming a project-wide inventory.

Read the project's Working docs and What's next documents when present. For a
narrow task, read only the other documents and issues needed to do it well. Reconcile
material status claims against actual PRs, source revisions and verification, not
only issue labels or an old handoff.

## Choose the work

- To establish working-document storage, migrate files, or maintain a handoff, read
  [Working documents](references/working-documents.md).
- To answer what to do next, organize a batch, or refresh priorities, read
  [Prioritization](references/prioritization.md).
- During authorized project work, update affected issue evidence and documents at
  meaningful checkpoints. Refresh the queue when readiness changes and before
  handing off. This is maintenance during active work, not background automation.

A useful project has two distinct entry points: **Working docs** locates canonical
documents; **What's next** recommends actions from the live work state. Link both
from the project overview and link the queue from Working docs. Keep the document
catalog short; do not repeat the entire issue backlog there.

## Authority and scope

Issues own current status, acceptance criteria, blockers and a concise evidence
summary. Linked documents hold detailed reasoning, plans, decisions, verification,
handoffs and history. The queue owns recommended ordering and readiness explanations.
A ranked row is not a new task, an accepted public API, or a change to an issue's
priority or dependency edges.

Requests to set up or maintain project coordination authorize the corresponding
document and evidence updates within that project. Continue within existing
authorization; do not add a separate approval step for routine authorized edits.
Keep advice-only and read-only requests read-only. Managing the project does not
itself authorize implementing the queue, merging PRs, publishing releases, archiving
repositories, or sending messages to other people.

Preserve user decisions even when they reduce what is currently actionable. Record
the exact decision or external event needed to proceed. Do not turn a scheduling
preference into a hard dependency, or infer approval from a draft's presence.

Use the team's actual workflow and the user's completion policy. Distinguish
implemented, verified, In Review, merged and released. Update an issue only as far
as its observed evidence supports; a phase can finish while its issue remains open.
Reconcile umbrella issues from their own criteria and children rather than counting
them as independent implementation work.

## Reliable updates

Assign one writer per active document. Re-read before editing and prefer targeted
patches to replacing a large document from a cached copy. If an edit fails or a write
returns an uncertain result, retrieve the current document before retrying. Search
for an accepted creation before creating another copy. Preserve newer remote edits.

Use full repository URLs for GitHub issues and PRs. Bare numbers can resolve to
objects in another repository. Re-read after saves: check the target project, title,
canonical links, substantive content, code examples and any transformed references.
Titles can change a returned URL slug; use the current returned URL in new links and
retain document IDs as stable identifiers.

Put detailed verification in a linked evidence or handoff document: exact revisions
or artifact identities, commands or checks, outcomes and material limits. In the
issue, summarize the relevant result and any limitation affecting acceptance.
Distinguish observed failures, source-based hypotheses, known expected failures and
unsupported behavior. A passing regression gate does not establish that every case
succeeds. Keep enough evidence in shared storage to resume without a private checkout
or an expiring CI artifact. A small check can fit directly in the issue; create a
separate record only when the detail warrants it.

If access is unavailable, preserve drafts and the exact unsaved actions locally,
identify what could not be checked, and report that the shared state is not updated.
Do not silently treat a local fallback as the canonical remote record.

Finish with canonical links and a short account of what changed and what remains.
State whether maintenance is performed during work or by an actually configured
automation. Do not promise unattended synchronization.
