---
name: goal-orchestration
description: Coordinate long-running Codex goals with durable state and bounded delegation when the user explicitly requests $goal-orchestration.
---
# Goal orchestration

Treat the active goal as the completion contract. Explicit use of this skill authorizes
useful delegation within the goal's scope and host permissions. Use `$goal-prompting`
when the user only wants a prompt; do not start a goal merely because this skill is read.

## Durable state

Keep a short plan tied to the full goal and a durable deliverable ledger. Choose and
report the ledger location, including whether it is a deliverable or working artifact.
Track deliverables, status, delegated owners, evidence, verification results, and material
blockers. Record ownership transfers before another worker writes the same scope.

Inspect enough context to identify dependencies and useful work boundaries. Check required
access and tools before committing to an unattended phase. An optional tool or integration
is not a blocker when an available route satisfies the goal.

After compaction, interruption, or resumption, reconcile the goal, ledger, and actual
artifacts before continuing. Recover the whole deliverable set rather than replacing it
with the current local phase. Preserve completed work and unresolved decisions.

For measured optimization loops, keep the best result, latest experiment, outcome, and
next experiment in a running log. Ordinary implementation does not need an experiment log.

## Direct work and delegation

Choose direct work or delegation based on useful parallelism, context needs, and
integration cost. Keep the main thread responsible for integration and the final result.
Honor a goal that explicitly reserves the main thread for orchestration; otherwise it
may implement major deliverables directly when that is the simpler reliable approach.

Delegate independent bounded questions or disjoint write scopes. Give each worker the
necessary source paths, task, ownership boundary, expected result, and acceptance checks.
Pass only the context needed to preserve relevant decisions. Treat returned claims as
unverified until supported by source evidence or checks.

Bound concurrency to available host capacity. Keep dependent changes sequential. Use
isolated worktrees when shared writes would conflict. Use separate user-visible threads
when requested, or when supported and useful for durable independent workstreams;
subagents suit narrower tasks. Do not require unavailable thread tooling when native
subagents or direct work satisfy the goal.

If a worker stalls or fails, inspect its state and choose a narrower retry, replacement,
or direct takeover. Revoke or transfer write ownership before another worker edits that
scope. A replacement worker is optional, not a prerequisite to recovery.

## Decisions and authorization

Continue within existing scope and authorization. Ask only when a missing answer changes
the deliverable, a material decision, or permission for a consequential action and cannot
be resolved from available evidence. Existing authorization persists across phases and
workers. Do not silently expand into implementation, publishing, or production changes
when the goal authorizes only research or planning.

When a required action needs user input, complete independent authorized work and preserve
state. Report the concrete decision or action needed. A recoverable worker failure or
reconcilable artifact discrepancy is not itself a terminal blocker.

## Verification and completion

Accept each deliverable against the goal's criteria. Use affected checks while iterating
and required broader gates at their defined boundaries. Repeat a check when changes or
new evidence justify it, not merely because another worker or phase has started.

Use independent final review when it adds meaningful confidence and the host supports it;
honor any review explicitly required by the goal. Resolve findings against source evidence
and rerun affected checks. Extra agents or model effort do not broaden scope or redefine
completion.

Give concise progress updates at material milestones or changes in direction. Before
claiming success, reconcile every deliverable with its artifacts and required verification.
Report outputs, evidence, remaining risks, and any blocked requirements. Include detailed
delegation accounting only when requested or when it explains a material limitation.

Stop as blocked only when no reasonable in-scope route can reach the required result
without user input or an external change. Preserve exact state and report the smallest
needed intervention. Use the host's goal-status rules when recording terminal status.
Do not claim success because a first implementation exists or a tool merely accepted work.

Keep model and reasoning-effort selection in host configuration unless the user explicitly
makes it part of the task. Do not add model slogans or delegation quotas to the goal.
