---
name: goal-prompting
description: "Draft compact Codex /goal prompts with deliverables, context, and completion criteria. Does not execute the goal."
---

# Goal Prompting

Create compact, copy-ready `/goal` prompts. Treat the goal text as a durable completion contract: it should tell Codex what must be delivered, where to find context, and how to decide whether the goal is complete or blocked.

Do not execute `/goal` for the user. This skill only prepares the prompt they can paste into a goal.

## Core Rule

Keep `/goal` text small and outcome-focused. Codex uses goal text as both the starting prompt and completion criteria, and goal objectives must fit under 4,000 characters. Aim for 1,200–1,800 characters for ordinary goals and exceed that only when task-specific requirements materially need the space.

Prefer indirection:

- Put success criteria inline.
- Reference large context by path, URL, issue, repo, branch, or prior artifact.
- Reference reusable execution behavior with a skill, usually `$goal-orchestration`, instead of repeating its generic planning, ledger, delegation, recovery, progress, or review rules.
- Include task-specific process only when it changes the deliverable, ownership, dependency gate, or stop condition.
- Leave model, reasoning-effort, Pro, and Ultra selection to Codex or runtime controls; do not encode them in the goal.

## Workflow

1. Identify concrete deliverables, target paths, acceptance criteria, context sources, constraints, and blocked conditions.
2. Ask concise questions only when missing details would materially change the goal. Ask at most three at a time.
3. If the task is long-running, multi-deliverable, or delegation-heavy, include one compact reference such as `Use $goal-orchestration for durable state, bounded delegation, verification, and recovery.` in `Context`.
4. Add task-specific orchestration only when it changes ownership or execution. If the user wants the main thread to avoid bulk implementation, say so in one sentence. If the user requires user-visible separate Codex threads, state that plainly; otherwise let `$goal-orchestration` choose between subagents and threads.
5. When order matters, distinguish dependency-gated implementation from safe preflight, e.g. `Read-only preflight for later phases may run in parallel, but later-phase implementation must wait until the preceding phase handoff and verification gate are accepted.`
6. State blocked conditions as unresolved terminal conditions. Do not make a recoverable worker failure, missing optional tool, or reconcilable discrepancy an automatic blocker.
7. When orchestration adherence matters, require the final summary to disclose delegated agents or threads, major main-thread direct work, verification results, and unresolved risks.
8. Return one fenced `text` block beginning with `/goal`.
9. Keep any explanation outside the block brief.

## Default Shape

Use this shape unless the user asks for something different:

```text
/goal Deliver the following using the referenced context.

## Deliverables

- ...

## Context

- Use ...
- Use $goal-orchestration for durable state, bounded delegation, verification, and recovery.

## Stop Conditions

- Success means ...
- Stop as blocked if ...
```

## Section Guidance

`Deliverables` should name concrete outputs. Include paths, repositories, branches, files, or artifacts when they matter.

`Context` should point to source material and reusable process. Use references instead of pasting long specs. Reference `$goal-orchestration` once, then add only task-specific ownership, sequencing, verification, permission, or separate-thread requirements. Include exact verification commands when they are part of the completion contract.

If the user expects separate Codex threads rather than only subagents, state that plainly in `Context`; otherwise `$goal-orchestration` may choose either. If phases are dependency-gated, say whether read-only preflight may overlap while later-phase writes remain blocked.

`Stop Conditions` should be measurable enough for Codex to keep checking. Include one success condition per deliverable when useful. Block only when success is unreachable after reasonable in-scope fallback, such as required source material or access remaining unavailable or a product decision requiring the user. For orchestration-sensitive goals, require final reporting of delegated agents or threads, major main-thread direct work, and verification evidence.

## Output Rules

- Do not include broad generic orchestration instructions in the `/goal`; reference `$goal-orchestration` once, with only the task-specific constraints needed to shape ownership, sequencing, separate-thread use, verification, permissions, or stop conditions.
- Do not include unresolved placeholders unless the user explicitly wants a reusable template.
- Do not exceed 4,000 characters. If the goal cannot fit, ask whether to create or point at a file-backed instruction document.
- Do not name a model or reasoning effort or tell the model to think harder. Treat those as runtime configuration unless the user's deliverable is itself a model configuration.
- Use plain language and cut repeated words like "thorough", "comprehensive", and "complete" unless they are made measurable.
