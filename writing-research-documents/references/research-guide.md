# Writing Guide: Research Documents

Research documents capture what was learned during investigation of a problem,
technology, or area of the codebase.
They are the foundation for technical design documents and implementation plans.

* * *

## What a research doc is for

A research doc answers the question: **“What do we need to understand before we can
design a solution?”**

It gathers and organizes information that would otherwise live only in someone’s head or
scattered across spec PDFs, source files, and Slack threads.
A good research doc means the next person (or the same person three months later)
doesn’t have to redo the investigation.

## What a research doc is NOT

- **Not a design document.** Research may include design options and recommendations,
  but the purpose is to inform decisions, not to make them.
  Decisions belong in a technical design document (see the
  `writing-technical-design-documents` skill).
- **Not an architecture doc.** Research describes what was found at a point in time.
  Architecture docs describe the system as-built and are kept current.
- **Not a tutorial.** The audience is someone who needs to make technical decisions, not
  someone learning from scratch.

* * *

## Questions your research doc should answer

Not every question applies to every investigation.
Use the ones that fit.

**Problem and context:**
- What are we investigating and why?
- What prompted this research?
  (ticket, incident, new requirement, curiosity)
- What prior knowledge or assumptions are we starting from?

**Findings:**
- What did we learn? (This is the bulk of the document.)
- What exists today in the codebase?
  How does it work?
- What does the spec / standard / external documentation say?
- How do other implementations handle this?
- What are the constraints, gotchas, or surprising discoveries?

**Implications:**
- What design options does this research reveal?
- What are the trade-offs between them?
- What risks or open questions remain?
- What do we recommend, and why?
  (only for doc types that end in a recommendation — technology evaluations, root cause
  analyses, comparative analyses; neutral surveys recommend only when asked)

* * *

## Structural patterns

Research docs vary widely in shape.
Below are structural patterns that tend to work well.
Mix and match based on what your investigation demands.

### Spec + codebase + design (the full treatment)

For adding a new protocol feature or capability where you need to understand the
specification, survey the existing codebase, and sketch possible designs.

```
1. Background (what and why)
2. Specification analysis (wire formats, sequences, requirements)
3. Current codebase architecture (what exists, how it works)
4. Design options (candidate approaches, sketches, trade-offs — informing the future
   design document, not making its decisions)
5. Risks and open questions
Appendix: comparisons, reference tables
```

### Codebase survey

For understanding how an existing subsystem works, often as preparation for modifying it
or debugging it.

```
1. Question / objective
2. Component inventory (what exists, where it lives)
3. Data flow / control flow (how the pieces interact at runtime)
4. Key observations (non-obvious behavior, edge cases, assumptions)
5. Implications for the planned work
```

### Investigation / root cause

For debugging a specific problem — session leaks, performance regressions, intermittent
failures.

```
1. Symptoms (what was observed, when, under what conditions)
2. Hypotheses considered and how each was tested (including ruled-out ones, with the
   evidence that eliminated them — this saves the next investigator the same dead ends)
3. Findings (what was actually happening and why)
4. How the root cause was confirmed (reproduction, failing test, instrumentation, log
   correlation — or an explicit statement that it remains unconfirmed and what evidence
   supports it; a causal claim backed only by code reading is a hypothesis, not a
   finding)
5. Contributing factors (what made this possible or hard to detect)
6. Recommended fix or next steps
```

### Technology evaluation

For evaluating a library, tool, or approach before committing to it.

```
1. Problem / need
2. Candidates evaluated (with versions — the evaluation is meaningless later without
   knowing what was evaluated)
3. Hard requirements (disqualifying if unmet) and evaluation criteria (with relative
   importance)
4. Per-candidate analysis (capabilities, trade-offs, fit)
5. Recommendation
```

### Comparative analysis

For understanding how multiple implementations (other SDKs, competing libraries,
internal services) solve the same problem.

```
1. What we're comparing and why
2. Per-implementation summary (with the version or commit surveyed, and when)
3. Comparison matrix
4. Patterns and divergences
5. What this means for our approach
```

* * *

## Conventions

These are the few things that should be consistent across all research docs, regardless
of structure.

**Title and opening.** Start with a clear title and a one-to-two sentence summary of
what was investigated and why.
The reader should know within 10 seconds whether this document is relevant to them.

**References.** Link to specifications, external documentation, related research, and
relevant source files.
Put these near the top (after the summary) or in a dedicated references section — the
reader shouldn’t have to hunt for them.

**File references.** When citing codebase locations, use `path/to/File.ext` with line
numbers where precision matters.
In GitHub-linked repositories, prefer permalinks using the commit hash — once pushed,
these survive branch movement and rebases (a permalink to an unpushed commit is a dead
link for every reader).
Local paths are fine when GitHub isn’t available; they go stale but are still valuable
when the research is fresh.

**Date and context.** Generated automatically by the `research-metadata.sh` script as
YAML frontmatter (date, git commit, branch, repository, dirty-tree flag).
This helps future readers gauge staleness and trace findings back to the exact codebase
state.
The frontmatter commit pins only the researched repository — record versions of external
candidates, other repos, or vendored code in the body where they are discussed.

**Table of contents.** Include one for documents longer than a few screens.
The reader may need only one section.

* * *

## Quality signals

A good research doc:

- **Distinguishes fact from interpretation.** “The spec says X” and “the code does Y”
  are facts. “We should do Z” is interpretation.
  Keep them visually and structurally separate.
- **Shows its work.** Include the evidence — code snippets, spec quotes, test results —
  not just conclusions.
  The reader needs to be able to evaluate your reasoning.
  “Sessions are closed in `SessionManager.close()` (SessionManager.java:412), called
  from both the watchdog and RPC teardown paths” is evidence; “the session manager
  handles cleanup” is not.
- **Marks confidence.** Distinguish verified findings (re-read at the cited lines,
  executed, reproduced) from inferences and secondhand claims.
  A designer building on the doc needs to know which is which.
- **Names what it doesn’t know.** Explicit open questions are more useful than false
  completeness. A clear “I don’t know X and it matters because Y” saves the next person
  from rediscovering the gap.
- **Is searchable.** Use specific, descriptive section headings.
  Someone grepping for “idle socket” or “certificate discovery” should land in the right
  place.
- **Earns its length.** Long is fine if the investigation is complex.
  But every section should carry its weight.
  If a section exists only because “research docs usually have one,” cut it.
