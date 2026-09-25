# Prioritization

Read this when selecting the next task, proposing a batch, or maintaining What's next.

## Ground the queue

Inspect the requested project's issues, priorities, descriptions, acceptance criteria,
parents and dependency relations. Check PR state and verified source prerequisites
where they affect readiness. Reuse current research and decisions; recheck external
evidence when the recommendation depends on a release or publisher change.

Formal dependency links are only part of readiness. Account for:

- External releases, publisher corrections, access and unresolved product decisions.
- Prerequisites implemented and verified in an open stack but absent from the default
  branch. Name the exact usable base; In Review does not mean merged or unusable.
- Phased issues with actionable early work and a later external wait. Do not hold the
  actionable phase unnecessarily or call the entire issue complete after that phase.
- Work already fixed upstream that now needs adoption and downstream verification.
- Umbrella issues whose concrete children carry the executable work.
- Shared files, public contracts and baseline updates that make parallel integration
  unsafe even when the issue graph contains no edge.

Distinguish a real prerequisite from a preferred sequence. Correct issue dependency
links only when the relationship is established and the requested coordination scope
allows it. Keep inferred constraints labeled until confirmed.

## Recommend useful work

Lead with one concrete next action and why it is preferable now. Then provide a ranked
shortlist, normally three to five items when enough actionable work exists. Respect a
requested batch size; do not pad the list with blocked work or umbrella issues to reach a number.
Conditional candidates can appear if their readiness is explicit.

For each shortlisted item, give its issue link, reason, readiness and first bounded
step. Use the existing issue for full acceptance criteria. Rank using judgment about
explicit user commitments, verified correctness risk, dependency unlocks, feedback
cost and integration effort. Do not invent estimates or apply an unexplained score.

Keep the top recommendation visible without making the reader traverse the dependency
graph. Include independent alternatives for when the main workstream is occupied.
List waiting work separately with the actor, decision, artifact or event that would
make it actionable. Explain later dependency chains only enough to show what the
current work unlocks; do not reproduce the entire backlog as a second tracker.

Examples of useful distinctions:

- A runtime upgrade's first phase is ready; its later release-dependent phase waits
  for published artifacts and verified fix inclusion.
- A naming repair can start on a reviewed prerequisite branch while integration into
  the default branch still awaits review and merge.
- An issue has no blocking edge but cannot be repaired correctly until a publisher
  clarifies the intended model identity.
- Two ready client-accessor fixes need serialized edits to a shared emitter, while
  a parser regression can proceed in a separate worktree.

Preparation, investigation, implementation and final verification can have different
readiness. Name the phase that can start. Documenting parallel opportunities does not
itself authorize spawning agents or starting implementation.

## Keep the queue live

Use one stable project document, linked from the overview and Working docs. Include
the reviewed timestamp and timezone, the baselines needed to act, and a short refresh
note explaining changed priorities or an unchanged order. Link detailed verification
from supporting records. Write the queue for someone choosing work: use plain terms
and keep each candidate to a few lines.

Replace the current ranking and refresh note in place. Do not prepend dated queues or
accumulate completed batches. Preserve material historical decisions in a linked ledger
or frozen handoff, keeping this document focused on the next action and current waits.

The coordinating agent refreshes it before selecting a task or batch, when meaningful
changes affect readiness, and before handoff. Relevant events include completed work,
review/merge, new defects, dependency changes, decisions and external resolutions.
Do not rewrite it after every tool call. Unless separately configured, updates happen
during active work, not through an unattended watcher.

At a refresh:

1. Reconcile the relevant live sources. For a project-wide ranking, check the full
   issue inventory; an established queue can use focused reads when the scope is narrow.
2. Remove completed items, carry unfinished phases forward, and distinguish review
   from merge. Avoid counting a child repair and its parent as two completed scopes.
3. Update the next action, ranked candidates, independent opportunities and specific
   waiting conditions. Explain material changes rather than silently shuffling ranks.
4. Record what was checked and what could not be verified. Mark affected entries stale
   when source access or new events invalidate their readiness. Revalidate the selected
   item before acting; a saved rank is not proof of current readiness.
5. Read back the document and links. Preserve historical handoff recommendations and
   point them to this live queue rather than rewriting past records.

Changing the queue does not change issue status, priority, ownership or dependencies
unless those updates are separately justified within the authorized task.
