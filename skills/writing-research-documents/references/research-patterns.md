# Research document patterns

Choose and adapt the smallest structure that serves the investigation. Combine patterns
when the question crosses domains. Do not fill headings mechanically.

- [Codebase survey](#codebase-survey)
- [Bug triage or root-cause investigation](#bug-triage-or-root-cause-investigation)
- [Specification plus codebase](#specification-plus-codebase)
- [Technology evaluation](#technology-evaluation)
- [Comparative analysis](#comparative-analysis)
- [Web or resource landscape](#web-or-resource-landscape)
- [Annotated resource collection](#annotated-resource-collection)
- [Idea exploration](#idea-exploration)

## Codebase survey

Use to understand an existing subsystem or behavior.

1. Objective and scope
2. Component inventory
3. Runtime data or control flow
4. Non-obvious behavior, constraints, and edge cases
5. Implications for the requested work
6. Open questions

## Bug triage or root-cause investigation

Use triage language until causality is confirmed. Code reading alone usually establishes a
hypothesis, not a root cause.

1. Symptoms and observation conditions
2. Evidence gathered
3. Hypotheses considered
4. Tests and ruled-out explanations
5. Confirmed cause, or current leading hypothesis with confidence
6. Contributing factors
7. Recommended next step or fix, when requested

Include reproduction, a failing test, instrumentation, history, or log correlation when
claiming a confirmed root cause.

## Specification plus codebase

Use when a protocol, standard, contract, or external requirement must be compared with an
implementation.

1. Background and scope
2. Relevant normative requirements
3. Current implementation
4. Requirement-to-implementation mapping
5. Gaps, ambiguities, and compatibility constraints
6. Design implications without making design decisions
7. Open questions

## Technology evaluation

Use when selecting a library, platform, service, or approach.

1. Need and constraints
2. Hard requirements and weighted evaluation criteria
3. Candidates with versions and evaluation dates
4. Per-candidate evidence
5. Comparison matrix
6. Recommendation and rationale
7. Risks and validation still needed

Do not recommend a candidate that fails a hard requirement merely because it scores well
elsewhere.

## Comparative analysis

Use to compare implementations, products, standards, or approaches without necessarily
selecting one.

1. Comparison question and common frame
2. Sources, versions, and dates
3. Per-subject summaries
4. Comparison matrix
5. Shared patterns and meaningful divergences
6. Implications
7. Unknowns that prevent a fair comparison

## Web or resource landscape

Use for broad web research, ecosystem surveys, and source aggregation.

1. Question, audience, and coverage boundary
2. Search method when reproducibility or exhaustiveness matters
3. Source landscape grouped by role or theme
4. Evidence-backed findings
5. Agreements, conflicts, freshness concerns, and gaps
6. Synthesis answering the original question
7. Recommended follow-up, when requested

Do not organize the document as a chronological search log.

## Annotated resource collection

Use when the durable artifact is primarily a curated set of resources.

1. Collection purpose and inclusion criteria
2. Resources grouped by use or theme
3. For each resource: authority, freshness, relevance, and unique contribution
4. Duplicates, conflicts, and notable omissions
5. Synthesis: which resources to use for which need

A bare link list is incomplete.

## Idea exploration

Use to examine an early idea without prematurely turning it into a design.

1. Idea and motivating problem
2. Assumptions that must hold
3. Existing analogues, evidence, or prior art
4. Potential value and constraints
5. Alternative framings or approaches
6. Risks, unknowns, and decision criteria
7. What should be researched or decided next

Keep possibilities distinct from evidence that they will work.
