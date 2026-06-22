---
name: dynamic-workflow-prompting
description: "Draft and refine a compact, copy-ready prompt that a user pastes into Claude Code to kick off a dynamic workflow — multi-agent orchestration run by the Workflow tool. Use when the user wants a prompt that triggers a workflow, wants to turn messy notes or a goal into a workflow request, asks how to structure a request that fans out subagents in parallel, or needs a prompt that states deliverables, referenced context, success and stop conditions, and the authorization that lets Claude launch a workflow. Produces the trigger prompt only; it does not run the workflow."
---

# Dynamic Workflow Prompting

Produce a compact, copy-ready prompt that a user pastes into Claude Code to kick off a
**dynamic workflow** — multi-agent orchestration run by the Workflow tool. The prompt is
a completion contract: it tells Claude what to deliver, where the context lives, what
"done and verified" means, and that it is authorized to fan out subagents.

Prepare only the prompt. Do not call the Workflow tool or run anything in this skill.

## What the prompt is — and isn't — for

The Workflow tool already knows *how* to orchestrate. Its own guidance — always in
context when the tool is available — covers pipeline-vs-parallel, structured outputs,
adversarial verification, loop-until-dry, resume, worktree isolation, and the rest. So a
good dynamic-workflow prompt does **not** re-teach any of that. Re-explaining the
mechanics just bloats the prompt and competes with knowledge Claude already has.

The prompt's job is the part the tool *can't* infer:

- **The deliverables** — what concrete outputs to produce.
- **The context** — where the source material is (by path, URL, or issue, not pasted).
- **The fan-out unit** — the natural thing to parallelize over, if there is one.
- **Done means** — measurable success per deliverable, how to verify, when to stop blocked.
- **The authorization** — the phrase that lets Claude launch a workflow at all.

Keep it small and outcome-focused — but *small* means no pasted context and no workflow
mechanics, not few deliverables. A ten-module build earns a long contract; cut words, not
deliverables or checks. Everything else, Claude supplies.

## The authorization line is load-bearing

The Workflow tool only runs when the user has **explicitly** opted into multi-agent
orchestration. Without an authorization phrase, Claude answers inline and never launches a
workflow. Every prompt this skill produces must carry one:

- `Use dynamic workflows to orchestrate this.`
- `Fan out subagents in parallel.`
- The one-word opt-in: `ultracode`.

Prefer the plural — *dynamic workflows* — to signal that Claude may use as many workflows
as the work needs rather than cramming everything into one: sequenced across the overall
phases (survey → design → implement → review, reading each result before the next),
dedicated to a single deliverable that is itself a project with its own design → plan →
implement cycle, or nested within a stage big enough to fan out. The prompt should not try
to plan these out up front — naming the deliverables and their success conditions is
enough; the decomposition is discovered during the run. Pair it with a push for depth —
`push for a thorough, verified result` — so each workflow defaults to a real fan-out
rather than a token one.

## What makes a prompt good for fan-out

- **Name the fan-out unit when there is one.** "One slice per file / per endpoint / per
  finding" gives the workflow its parallelization axis. If the work has no natural unit,
  say what the phases are instead (e.g. survey → verify → synthesize).
- **Pin down scope words.** "Thorough", "complete", "broad", "limited", "key", "core",
  "where appropriate" each let the workflow pick its own boundary — usually a smaller one
  than you meant. Replace them with a check or an enumeration: not "broad client coverage"
  but "every monitor, command, and interrogation message type"; not "unsigned fields where
  appropriate" but the rule that decides. These are what the workflow self-checks against.
- **Give every deliverable a check — especially the soft ones.** Cross each deliverable
  off against the success conditions; one with no way to verify it (docs, examples,
  "production-quality") gets done shallowly or skipped. Pin a concrete check even for prose
  outputs: the docs cover the named sections, the examples compile and run.
- **Reference context, don't paste it.** Fan-out agents need to know *where* to look;
  pasting long specs into the prompt wastes the budget that should go to the work.
- **Ask for a fan-out report.** Have the result state what was produced, how it was
  fanned out, and the verification evidence — so you can tell it actually orchestrated and
  checked itself rather than answering inline.

## Workflow

1. Identify deliverables, context sources, constraints, blocked conditions, and any
   natural fan-out unit or phase structure.
2. Ask at most three concise questions, and only when a missing detail would change a
   deliverable or the fan-out shape.
3. Lead with the outcome. Reference bulk context by path, URL, or issue.
4. Include the authorization line plus a push for a thorough, verified result.
5. State measurable success per deliverable, how to verify, and when to stop as blocked.
   Ask for a short fan-out report.
6. Return one fenced `text` block with the prompt. Keep any explanation outside it brief.

## Default shape

Use this shape unless the user asks for something different:

```text
[Outcome sentence — what to produce, using the referenced context.]

Use dynamic workflows to orchestrate this — fan out subagents in parallel, and use as many
workflows as the work needs (across phases, per heavy deliverable, or nested within a
stage), pushing for a thorough, verified result.

## Deliverables
- ...

## Context
- Use <paths / URLs / issues / prior artifacts>.
- Fan out one slice per <file / endpoint / finding>.   # omit if there's no natural unit

## Done means
- Success: <one checkable condition per deliverable>.
- Verify by <commands / checks>.
- Stop as blocked (don't claim success) if <missing source / no access / a decision needs me>.

## Report
- What was produced (paths / artifacts), how it was fanned out, and verification results.
```

## Section guidance

`Deliverables` name concrete outputs, with paths or artifacts when they matter — one
checkable success condition each. A deliverable can be broad enough to be its own project:
"a separate repository with Docker images for a foo-library client and server, usable for
interop testing" implies its own design → plan → implement cycle. State it as an outcome
and let it become its own workflow when Claude reaches it — don't pre-decompose it in the
prompt or expect a single top-level pass to plan it.

`Context` points to source material and names the fan-out unit. Don't paste long specs;
reference them. Include exact verification commands here if the work needs them.

`Done means` is what lets the workflow check itself and stop correctly. Give a success
condition per deliverable, a way to verify, and blocked conditions — missing source
material, failed access, an unavailable tool, or a product decision that needs the user.
Read the success list against the deliverable list before finishing: a deliverable that
appears in one but not the other is a coverage gap the workflow will fall into.

`Report` keeps the run honest: a result that can't say how it fanned out or what it
verified probably didn't.

## When NOT to recommend a workflow

A dynamic workflow is for work that fans out — many files or sources to cover, independent
slices, or a find → verify → synthesize shape. If the task is a single linear edit, one
lookup, or a quick conversational answer, say so and skip the workflow; the prompt should
just ask Claude directly. Don't manufacture parallelism that isn't there.

## Output rules

- Always include an authorization phrase; without it the Workflow tool won't fire.
- Don't explain how to write the workflow — Claude already knows. Give it the contract.
- Don't leave unresolved placeholders unless the user wants a reusable template.
- Use plain language; replace scope words ("thorough", "broad", "where appropriate") with
  a measurable condition — a count, an enumeration, or a per-deliverable success line.
