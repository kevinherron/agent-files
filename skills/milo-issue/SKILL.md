---
name: milo-issue
description: Analyze, plan, and fix Eclipse Milo issues through a tested PR and Greptile review cycle. Use autonomous mode for straightforward fixes or proposals mode to choose a direction before implementation. Also supports babysitting an existing Milo PR; respects analysis-only requests.
---

# Milo issue

Own the issue from understanding the failure to a PR Kevin can review. Explain the behavior and decisions simply. Do not hand back routine implementation, verification, or review follow-up work.

## Modes and scope

Accept an issue URL/number, a PR with a suggested fix, or a concrete failure report. Infer the repository from the link and checkout; Milo's upstream is `eclipse-milo/milo`.

| Mode | Use when | Decision point |
| --- | --- | --- |
| `autonomous` | The failure and intended behavior are clear, and a bounded fix can preserve the existing contract. A suggested fix is a starting hypothesis to verify. | Proceed through implementation, commit, PR, checks, and Greptile review. Notify Kevin when ready. |
| `proposals` | The user asks for alternatives, or meaningful API, compatibility, ownership, specification, or resource tradeoffs need a choice. | Investigate first, present one or more concrete directions, recommend one, and wait for selection before implementing the production fix. Then continue through the same delivery cycle. |

Honor an explicit mode. Otherwise choose after initial investigation and state the choice briefly. If an autonomous fix reveals an unresolved material design choice, present that choice with evidence instead of guessing. Do not interrupt for routine implementation details.

`$milo-issue <issue URL>` requests the full workflow. Additional context such as "compare with .NET" or "double-check the spec" adds investigation requirements; it does not reduce the task to analysis unless the user says so. Complete that investigation, then continue or ask the concrete design question needed to proceed. Do not end with an unresolved compatibility concern and leave Kevin to restart the workflow.

An explicit invocation to fix an issue using this workflow authorizes scoped commits, pushing a feature branch, creating/updating its PR, posting review replies, and requesting Greptile re-review. In proposals mode, this delivery authorization takes effect after the direction is selected. Do not ask again at each step. Implicit skill selection does not itself grant publication or messaging permission; use the user's actual request and existing authorization.

Narrower requests retain their boundaries. "Analyze only", "proposals only", "do not commit", or "local fix only" stop at the requested deliverable. Babysitting an existing PR starts with its current diff and review state; it does not authorize replacing its design or opening a duplicate PR. Read-only PR review remains read-only. Do not merge, release, or publish snapshots without an additional instruction. Carry forward later merge authorization without asking again, after the completion checks pass.

A requested draft PR is a deliberate handoff. Preserve its draft state and report review/check coverage accurately; do not mark it ready just to trigger Greptile. Resume the full review cycle when the user asks to continue or take it out of draft.

## Establish the problem

1. Read the checkout's `AGENTS.md` and applicable nested guidance. Inspect branch, working tree, remotes, and current revision. Preserve unrelated changes; reuse a suitable task worktree or create an isolated one when needed.
2. Read the full issue, comments, linked PRs, and relevant existing reviews. For a PR, inspect the actual diff and base. Resolve the target branch from user instructions and current issue/branch context; do not hardcode `main` or a historical integration branch. Fetch the selected base and check for overlapping fixes before editing. Briefly identify the base and revision being used. If a related fix lands during the work, reassess integration and affected tests before publishing; distinguish verification before and after the base update.
3. Trace the failing path and identify the caller-visible contract. Distinguish observed behavior, root-cause evidence, the reporter's proposed repair, and unanswered questions. Check the applicable OPC UA specification when required behavior is uncertain, including its version and encoding mode. Link the supporting section when it affects the decision.
4. Reproduce the failure with the smallest useful regression. For a bug fix, demonstrate failure on the unfixed implementation and success after the repair where feasible. A broken fixture, setup failure, or passing process that catches and logs an error does not establish the regression. Say what could not be reproduced.
5. Explain the trigger, actual result, expected result, and mechanism in a short paragraph. Use a tiny flow or code-shape sketch if that makes the explanation easier to follow. Establish why a repair is needed before choosing its implementation.

Prefer changes within the existing API and proper owner of the behavior. Avoid adding encoding-specific hooks to shared interfaces merely to accommodate one implementation. These are preferences, not reasons to hide a necessary API change or force an awkward internal workaround.

When comparing another stack, pin the source revision and distinguish generated codecs from runtime-generated codecs. Separate source tracing from executed interoperability tests. Use the applicable specification and independent wire/schema expectations as the authority; another implementation or an existing passing test can preserve the same defect. Compare stacks when requested or when it would resolve a real design uncertainty, not as a mandatory detour for every fix.

Investigate both sides of a contract, such as encoder and decoder, producer and consumer, or validation and invocation. Include tightly coupled changes needed for a coherent fix; explain their relationship. Separate nearby independent defects and material scope expansions for a decision. Do not equate an intentionally unsupported mode with a bug, or promise universal round trips from a few reversible values.

## Present directions when needed

In proposals mode, finish enough investigation to make the choice concrete. Do not stop at a list of ideas or ask Kevin to design the fix.

- Lead with the shared diagnosis and your recommendation.
- Before recommending a shared API addition, evaluate whether existing registration, codec metadata, or an encoding-local adapter can express the missing information. Explain why that route works or fails. Compare materially different designs, not only two syntactic forms of the same API addition.
- Explain each viable direction in terms of changed behavior, responsibility, and approximate code shape. Identify the important classes or interfaces without listing every file.
- Compare API/source/binary compatibility, wire behavior, implementation complexity, runtime costs when relevant, and the tests that would distinguish success. State the adoption work: whether existing codecs still work, registration must change, or generated code must be regenerated. Label unknowns; do not invent performance claims.
- Evaluate the issue's suggested fix. Add one or two alternatives when useful or requested, but do not manufacture weak options to fill a quota.
- Show the smallest useful before/after diff, pseudocode, call tree, or comparison table beside the explanation.
- End with the concrete choice. Wait for it before changing production behavior. Read-only investigation and isolated reproductions can continue.

Once selected, restate the resulting scope briefly, including any coupled fixes, then proceed. If follow-up discussion changes the scope, explain the final combined behavior again so Kevin does not have to reconstruct it from earlier alternatives.

A concise in-conversation implementation plan usually suffices. Use `writing-implementation-plan-documents` when a durable Markdown plan is requested, not for every issue.

Keep implementation plans, probes, and workflow checkpoints local and uncommitted unless Kevin explicitly asks to publish them. A request to commit the fix or open a PR does not include those artifacts. Keep required package/API documentation and self-contained regression fixtures with the product change. Check staged paths and the outgoing commit range so a plan is not merely removed in a later commit while remaining in published history.

## Implement and verify

Use the repository's current Java conventions, test guidance, and documentation guidance. In Milo, read `.claude/docs/running-tests.md` and `.claude/docs/test-documentation-and-quality-guidelines.md` before tests, and `.claude/docs/documentation-guidelines.md` before Java/Kotlin documentation changes. Add or update `package-info.java` when required by `AGENTS.md`.

Keep the repair focused. Regression tests should establish behavior, preserve relevant rejection paths, and cover adjacent boundary cases that could invalidate the fix. For codecs, combine independently expected wire output with decoding/round-trip coverage where the format supports it. Two mutually incorrect implementations can pass a round trip. Check reader position or a following field when token consumption matters. Use deterministic coordination for concurrency tests instead of timing-dependent sleeps.

Delegate **every Maven command** to a worker following `.codex/agents/maven-command-runner.md`. Supply the exact worktree and commands. The runner executes and reports; the parent diagnoses, edits, and decides what to rerun. If delegation is unavailable, report the verification blocker rather than running Maven directly.

Before committing, complete the repository's required verification, including:

```text
mise exec -- mvn -q spotless:apply
mise exec -- mvn -q clean compile
```

Run the meaningful targeted tests and required module/reactor checks using the documented flags. Recheck after fixes as appropriate. Inspect formatter changes before staging. Record actual results and material limits; compilation alone does not establish the bug is fixed.

If the user requests an independent pre-commit review, delegate a read-only review of the actual diff, expected contract, and regression coverage. Resolve actionable findings before committing. This is optional unless requested or required by applicable repository guidance.

## Commit and open the PR

Use `writing-commit-messages` for commits and `create-pr` for creating or updating the PR. Read those skills when entering their stages. Follow their scope, base-selection, publishing, and readback guidance.

Keep commits coherent, including supporting tests and docs. Explain the concrete failure and reason for the fix in plain language, not a file inventory. Small commit messages need no elaborate body or diagram.

The PR description must stand alone for an engineer who missed the conversation:

- Lead with the trigger and before/after behavior, then explain the mechanism. For subtle wire-format or namespace changes, show one small actual-versus-correct example before introducing abstractions such as model-to-schema mappings. State what callers must change, if anything.
- Borrow `show-me` concepts: a short diff for changed code shape, pseudocode for a rule, or a small call tree/Mermaid diagram for ownership and flow. Use only what clarifies this change and renders in GitHub Markdown. Label illustrative snippets.
- Explain what the tests establish and any important limits. Put detailed commands after the explanation.
- Link the Milo issue when appropriate. Respect any user-specified boundary on private tracking or downstream context in public text.
- Rewrite the title/body when the final scope changes. Do not append a diary of abandoned directions or let the first description become inaccurate.

Use simple sentences, concrete examples, sentence-case headings, and straight quotes. Avoid em dashes, inflated claims, repetitive headings, and jargon that the reviewer must decode.

After publishing, read back the PR and proceed directly to [the review cycle](references/review-cycle.md). Creating the PR is not the completion point for the full workflow.

## Finish

Report "ready for your review" only when the latest pushed revision has passing required checks, a completed Greptile review cycle, and no unaddressed actionable findings. Distinguish findings fixed from findings refuted with evidence. A high bot score or no comments yet is not sufficient.

Notify Kevin in the current conversation with the PR link, a short explanation of the fix, verification and review status, and any remaining limitation. No separate email or chat notification is implied. If blocked, report the exact pending decision or external condition and preserve the resumption state described in the review reference. Do not describe a blocked PR as ready or promise background monitoring after the session ends.

## Example requests

```text
$milo-issue autonomous https://github.com/eclipse-milo/milo/issues/NNNN
Use the suggested fix if it holds up. Let me know when the reviewed PR is ready.

$milo-issue proposals https://github.com/eclipse-milo/milo/issues/NNNN
Compare the suggested fix with alternatives that preserve the public API.
Once we choose, take it through the PR and Greptile cycle.

$milo-issue babysit https://github.com/eclipse-milo/milo/pull/NNNN
Address or refute feedback and re-request review after pushing fixes.
```
