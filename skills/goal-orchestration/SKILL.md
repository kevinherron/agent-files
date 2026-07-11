---
name: goal-orchestration
description: "Coordinate long-running Codex goals when the active goal or prompt explicitly asks to use $goal-orchestration. Use for multi-deliverable work that authorizes a main-thread orchestrator/integrator, durable deliverable tracking, compaction-safe recovery, bounded parallel work with subagents or separate threads, owned work scopes, evidence gathering, verification, unattended execution, final readiness review, and clear success or blocked reporting. Do not use merely because any /goal exists; use $goal-prompting to draft /goal text."
---

# Goal Orchestration

Run long Codex goals with the main thread as orchestrator/integrator and the active goal text as the completion contract. Treat explicit `$goal-orchestration` in the goal or prompt as authorization to delegate proactively when work divides into independent read-only or disjoint write scopes. Keep dependency-gated work sequential and synthesize parallel results before acting on them.

Use `$goal-prompting` instead when the user only wants help drafting a `/goal` prompt.

## Start Of Goal

1. Restate the goal's deliverables, referenced context, stop conditions, constraints, and likely verification surfaces.
2. Create a short phase plan and keep it updated as facts change.
3. Choose and disclose a durable ledger path or persistence surface, including whether it is a deliverable or a working artifact. Record deliverable, owner, status, evidence, verification command, unresolved risks, and ownership-change notes. Keep it aligned with the goal's stop conditions.
4. Inventory enough files, repositories, docs, prior artifacts, tools, and commands to delegate work intelligently.
5. Preflight mandatory unattended dependencies: permissions, sandbox and network access, credentials, interactive approvals, external services, and commands. Distinguish unavailable optional tooling from a required blocker.
6. Identify the current work layer—research, design, implementation, review, verification, or external coordination—and do not silently move into another layer unless the goal authorizes it.
7. Ask the user only when an answer is required to choose the deliverable, scope, external side effect, or blocked resolution.

## Plan And Ledger

Keep the top-level plan tied to the full goal contract. Nested phase plans are allowed, but do not replace the top-level plan with a narrower local phase such as "finish Docker validation" while the full goal is still active.

Use stable identifiers that match the goal's deliverables and phases. Name internal slices as work packages or review passes rather than reusing goal-level phase numbers. For separate threads, record the thread ID, environment or worktree, branch when relevant, and integration state.

Update the ledger immediately after any ownership change, failed delegation, main-thread takeover, completed verification, or newly discovered blocker. Do not let the ledger trail materially behind the source evidence; it is the recovery surface for compaction and handoff.

For iterative optimization or experiment loops, keep a separate running log with the current best result, the last change, what the evaluation improved or regressed, and the next experiment. Do not add this artifact to ordinary implementation work unless repeated measured iteration requires it.

After context compaction, resume, interruption, or thread transition:

- Re-read or reconstruct the active goal's deliverables, context, stop conditions, and verification surfaces before continuing.
- Rebuild the full deliverable ledger from available thread summaries, files, and source evidence.
- State what top-level deliverables are complete, in progress, pending, blocked, or intentionally deferred.
- Continue from the current phase only after confirming it still serves the full goal contract.

## Execution Economy

- Use the fewest useful tool loops consistent with correctness, required evidence, calculations, and citations.
- After each material result, decide whether the current deliverable can now be accepted. If not, identify the smallest missing fact or next action.
- Parallelize independent reads and disjoint write scopes. Keep work sequential when one result determines the next action, then synthesize parallel outputs before further changes.
- Do not repeat unchanged searches, reviews, builds, or verification commands. After a local fix, rerun affected checks; run the complete gate at the required phase or final boundary.
- Try at most two meaningfully different fallbacks for the same failure unless new evidence changes the diagnosis. Then choose a recorded main-thread takeover, a different owned approach, or a genuine blocked stop.
- Additional model effort or multi-agent capacity does not broaden scope, permissions, verification requirements, or the definition of done.

## Main Thread Role

Keep the main thread focused on orchestration:

- Decompose work into bounded phases and ownership scopes.
- Assign focused subagents or separate threads when work divides cleanly and parallelism materially reduces latency, isolates risk, or improves evidence.
- Before non-trivial edits, assign an owner for each major deliverable or explain why that deliverable must remain on the main thread.
- Resolve cross-cutting decisions, contradictions, integration risks, and user-facing tradeoffs.
- Synthesize summaries from delegated work instead of flooding the main thread with raw exploration output.
- Do direct work only when it is small, unblocks delegation, integrates outputs, resolves conflicts, handles a clear local fix discovered during verification, or prepares the final evidence summary.
- Do not author whole major deliverables directly when they could be delegated under clear ownership boundaries, unless delegation is blocked or would create unacceptable integration risk.
- If a delegated worker stalls, fails to checkpoint, or produces no usable files, first narrow the scope and try one meaningfully different replacement subagent or separate thread before taking over a major deliverable in the main thread. Direct takeover requires a short reason in the ledger and final report.

## Delegation

Use subagents or separate threads for bounded context extraction, research, implementation slices, verification, review, documentation, and final readiness checks when the work has a clear owner and acceptance surface.

Use separate Codex threads, not only subagents, when the goal explicitly asks for user-visible threads, when workstreams are durable enough that the user should inspect or continue them independently, or when isolated worktrees/branches materially reduce write-conflict risk. Prefer separate threads for large independent deliverables such as transport modules, integration-test suites, docs/examples, interop repositories, or long-running implementation slices. Use subagents for narrower read-only, review, short-lived, or tightly scoped worker tasks.

Give each delegated agent:

- A focused task.
- Concrete files, directories, repositories, branches, docs, or artifacts.
- The current work layer and explicit non-goals.
- Ownership boundaries for any writes.
- Expected output format.
- Required commands or inspection surfaces.
- Reporting requirements: changed paths, commands run, results, risks, open questions, and nested delegation summaries.

Pass the smallest sufficient context. Prefer a self-contained task with referenced paths and a limited conversation fork; use full-history inheritance only when the worker genuinely needs the complete prior decision trail.

For write-heavy work, avoid overlapping edits. Prefer disjoint scopes or isolated worktrees/branches. The main thread owns final integration unless the goal states otherwise.

Subagents and separate threads may make local decisions inside their delegated scope. Ask the user before irreversible external changes, publishing, spending money, deleting data, or modifying production systems.

## Unattended Runs

- Surface mandatory approval, access, credential, network, or external-service requirements before committing to a long unattended phase.
- Do not treat an optional integration, ecosystem check, or replaceable tool as mandatory unless the goal says it is.
- If a mandatory step cannot run unattended, complete all safe independent work, preserve exact state in the ledger, and report the smallest user action or external change needed.
- Do not broaden permissions, external side effects, or production scope merely to keep the goal running.

## Progress Updates

Before the first tool call, give a short user-visible preamble that states the first step. During execution, update at major phase changes or when a finding changes the plan. State one concrete outcome and the next step; do not narrate routine tool calls. Intermediate updates never satisfy the goal's completion contract.

## Evidence And Review

Prefer small, verifiable increments. After each major phase, collect results, resolve contradictions against source evidence, and update the plan.

Before reporting success:

- Check every deliverable against the goal's stop conditions.
- Check the durable deliverable ledger and include owners, evidence, verification results, and unresolved risks in the final synthesis.
- Run or delegate required verification commands.
- Perform one independent final readiness review for non-trivial goals; repeat it only when findings require material follow-up.
- Report completed deliverables, exact paths or artifacts, commands and results, unresolved questions, blockers, intentionally deferred non-goals, delegated agents or threads used, and any major work the main thread implemented directly.
- Disclose the rough balance of delegated work versus main-thread direct work by deliverable or major phase, especially after worker failures or main-thread takeovers.

## Blocked Stop

Stop as blocked only when success is not reachable under the current context after reasonable in-scope fallback. A missing or contradictory artifact is not automatically blocking when accepted sources and current code can reconcile or repair it. Report:

- What was attempted.
- Evidence gathered.
- The specific blocker.
- The next user input or external change needed.

Do not mark success just because work was attempted. Do not keep running broad exploration when the next useful action depends on user input or an external state change.

## Model And Effort

Keep this skill model- and effort-agnostic. Do not add instructions to think harder, use Pro mode, or use a named reasoning effort to the goal contract. Configure model, effort, and multi-agent mode through Codex or runtime controls and compare settings with representative evaluations when tuning them.
