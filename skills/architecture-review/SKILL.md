---
name: architecture-review
description: "Review a codebase and produce an architecture review with an ordered refactoring plan. Covers the whole codebase by default, or accepts an optional scope argument to narrow the review to a path, module, or feature (e.g. '/architecture-review the OPC UA module', '/architecture-review Modules/driver-foo/'). Use this skill whenever the user wants a principal-architect-level assessment of an existing codebase, says 'review the architecture', 'do an architecture review', 'assess the codebase', 'write a refactoring plan', 'take over as architect', 'clean up the architecture', 'pay down technical debt', 'how should we restructure this', 'set this up for long-term development', or wants to step back from a feature-by-feature proof of concept and plan its path to maintainable, long-lived code. Produces a planning document only — no code changes in the pass that writes it."
---

# Architecture Review

Take over a codebase as its principal architect and produce a written architecture
review with a refactoring plan. The codebase was likely built iteratively, feature by
feature, optimizing for a working proof of concept — nobody has yet stepped back and
looked at the whole. Your job is to be that person.

The deliverable is a single document — default `docs/design/architecture-review.md` —
with four parts: current-state assessment, target architecture, refactoring plan, and
non-goals. **Planning only: make no code changes in the pass that writes the review.**
The plan is the artifact; implementing its phases is separate follow-up work.

## Scope

By default the review covers the **whole codebase**. The user can narrow it by passing a
scope argument when invoking the skill — the text after the command:

- `/architecture-review` — the entire codebase.
- `/architecture-review Modules/driver-foo/` — a **path**: review that directory.
- `/architecture-review the OPC UA module` — a **named module or subsystem**: locate it,
  then review it.
- `/architecture-review the new redundant connection feature` — a **feature** that may
  cut across modules: find the code that implements it and review that slice.

When a scope is given, first **resolve it to concrete code** — a set of files, packages,
or modules — before you judge anything; a named module or feature rarely maps to a single
directory. If the argument is ambiguous (it matches nothing, or several unrelated things),
ask the user to clarify before proceeding rather than guessing.

Then review that slice **and its boundaries with the rest of the system**. An architecture
review of a part is largely about how cleanly it fits the whole: its dependencies in and
out, the contracts it exposes, and the state it shares. Everything below applies to the
scoped area — the assessment, target architecture, and plan all concern that area, and the
codebase outside it becomes an explicit non-goal.

## Stance

The quality of the review lives or dies on these:

- **Understand before you judge.** Explore until you genuinely understand the system,
  not until you have enough to form an opinion. The first impression is usually
  incomplete and often wrong.
- **Assume nothing was deliberate.** Reverse-engineer intent from the code, not from a
  charitable assumption that a structure exists for a reason. Much of it accreted.
- **Don't manufacture problems.** A convention you'd have chosen differently is not a
  defect. Every problem you name must cost something real — long-term velocity,
  correctness, or comprehensibility. If you can't state the cost, cut it.
- **Name what's sound.** A review that's all problems is untrustworthy and leaves no
  fixed points to build from. Call out what's already good and worth keeping.
- **Write as the implementer.** You are the person who will land these phases, not an
  outside consultant handing off a wish list. Every recommendation is something you'd
  be willing to do yourself.

## Phase 1 — Explore until you understand

Investigate the codebase across these dimensions. Ground everything in specific files,
classes, and functions — you'll cite them in the write-up.

- **Module boundaries & layering** — what the units are, whether they have clear
  responsibilities, whether layers are respected or bypassed.
- **Dependency flow** — which way dependencies point; cycles, inversions, a module
  that everything reaches into, leaked abstractions.
- **State & lifecycle management** — who owns what state, how it's mutated,
  initialization and teardown, concurrency and thread-safety, global/shared state.
- **Error handling** — how failures propagate, where they're swallowed, whether
  failure modes are consistent and observable.
- **Consistency of conventions** — naming, file/package structure, recurring patterns;
  the same problem solved three different ways is a comprehensibility tax.
- **Testability & tests** — seams for testing, what behavior is actually covered, how
  fast and deterministic the suite is, what's untestable by construction.
- **Build & tooling** — build system, dependency management, CI, formatting/linting,
  reproducibility, developer onboarding friction.

How to explore efficiently:

- Start from the entry points and the build/config files; map the module graph.
- Read the hot files — the largest, the most-depended-on, the most-churned.
- Trace one real operation end-to-end (a request, a job, a command) to see how the
  layers actually interact rather than how they're supposed to.
- Read the tests to learn the intended behavior and the contracts that must be preserved.
- Don't stop early. You understand it when you could explain the system to a new hire
  and predict where a given change would ripple.

For a large codebase, you may fan out exploration across subsystems (e.g. via the
Workflow tool, one agent per subsystem) — but the judgment and the final document are
yours to integrate, not a stapled-together set of agent reports.

## Phase 2 — Judge

Separate strengths from problems. Rank by impact on long-term velocity, correctness,
and comprehensibility; drop nitpicks entirely. For each problem, be able to state the
concrete cost and what it blocks. For each strength, state why it's worth preserving.

## Phase 3 — Write the document

Write to `docs/design/architecture-review.md` (create the directories). If the repo
already has a docs convention — `docs/adr/`, `documentation/`, a design folder — match
it and note where you put the file. For a scoped review, name the file for the scope —
`docs/design/architecture-review-opcua.md`, `architecture-review-driver-foo.md` — so
several reviews can coexist without clobbering each other.

Structure it as four sections:

1. **Current-state assessment** — the significant strengths and problems, each grounded
   in specific files/classes. Skip nitpicks; lead with what affects long-term velocity,
   correctness, and comprehensibility. Include the strengths explicitly — they're the
   fixed points the plan builds from.

2. **Target architecture** — where this codebase should end up, with your reasoning.
   Make decisive calls, not lists of options. Describe the intended module boundaries,
   dependency direction, where state and lifecycle live, the error model, and the
   testing strategy. Explain why this target beats the current shape, and say plainly
   what you're keeping.

3. **Refactoring plan** — an ordered sequence of phases, each **independently landable**
   (mergeable on its own, leaving the system working). For each phase, give:
   - **What changes** — the concrete edit, at the level of files/modules.
   - **Why** — which problem from §1 it resolves and which part of §2 it moves toward.
   - **Risk** — what could break, and how likely.
   - **Verification** — how you confirm behavior is preserved.
   - **Kind** — tag it a *pure refactor* (behavior-preserving) or a *functional change*.

   Sequence so earlier phases de-risk later ones — e.g. add characterization tests
   before restructuring the code they pin down. Include the testing, tooling, and
   infrastructure work, not just code movement. A phase you can't verify isn't ready.

4. **Non-goals** — what you considered changing and deliberately won't, and why. The
   rewrite you rejected, the imperfect convention you're keeping, the scope you're
   holding back. This is where you show judgment about what *not* to touch.

## Guidelines

- **Planning only.** No code changes in this pass — not even "quick" ones. The output
  is the document.
- **Scope.** Whole codebase by default; a scope argument narrows it to a path, module,
  or feature (see [Scope](#scope)). Resolve the argument to concrete code first, review
  that slice plus its boundaries with the rest, and ask to clarify only if it's ambiguous.
- **Cite everything.** Every strength and every problem names specific files or symbols
  and its concrete cost. Unsourced claims don't belong in the review.
- **Be decisive.** Recommend; don't enumerate options and defer. The target architecture
  is a set of calls, not a menu.
- **Independently landable is the bar** for every phase. If it can't ship alone or can't
  be verified, it's not a phase yet — split it or add the groundwork phase before it.
