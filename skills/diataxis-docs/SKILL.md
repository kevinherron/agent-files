---
name: diataxis-docs
description: Apply the Diataxis documentation framework to classify, write, revise, restructure, and review documentation around user needs. Use when Codex works on documentation writing, documentation revision, documentation classification, mode confusion, information architecture, README/API docs, tutorials, how-to guides, reference docs, explanations/conceptual docs, troubleshooting docs, onboarding docs, docs quality reviews, or requests such as "use Diataxis", "make this clearer", "turn this into docs", "organize these docs", or "split this mixed documentation". Do not trigger solely for ordinary code comments unless the user frames them as documentation quality, public docs, or documentation structure.
---

# Diataxis Docs

Use Diataxis as a practical user-need framework. Improve the document's fit to the reader's situation; do not force every docs set into four empty top-level folders.

## Operating Workflow

1. Identify the reader situation, task context, and documentation unit: whole docs set, page, section, paragraph, or suspicious sentence.
2. Classify the primary user need with the compass when the mode is unclear.
3. Choose one dominant mode per page or section. Allow small supporting fragments from other modes only when they do not interrupt the primary need.
4. Write, revise, restructure, or review according to the selected mode's form.
5. Preserve useful misplaced material by moving, splitting, shortening, or linking it rather than deleting by reflex.
6. Prefer incremental, high-confidence improvements for existing docs unless the user asks for a broader reorganization.
7. In final answers, mention the Diataxis classification only when it clarifies the decision, helps explain a review, or the user asked for Diataxis rationale.

Ask clarifying questions only when the primary mode would materially change the deliverable. Otherwise make a best-effort classification, state the assumption briefly if useful, and proceed.

## The Compass

Classify by user need, not by topic, audience seniority, or product feature.

| User relationship | Action: guides doing | Cognition: supplies knowledge |
| --- | --- | --- |
| Acquisition / study | Tutorial | Explanation |
| Application / work | How-to guide | Reference |

- Use **tutorial** for action + acquisition: "Teach me by guiding me through a safe learning experience."
- Use **how-to guide** for action + application: "Help me accomplish this real-world goal."
- Use **reference** for cognition + application: "Give me exact facts I can consult while working."
- Use **explanation** for cognition + acquisition: "Help me understand why, how, and how ideas relate."

Fast questions:

- Is the reader trying to learn by doing, or get work done?
- Is the content directing action, or supplying knowledge?
- Is the reader acquiring skill, or applying skill?
- Does the page answer "teach me", "how do I", "what is", or "why/about"?
- Would the reader consult this during work, or read it to build understanding?

## Mode Checklists

Use these as writing targets and review checks. During reviews, flag both missing items and intrusions from other modes.

### Tutorial

Write a guided lesson for learning by doing.

- State a concrete learner accomplishment.
- Use one safe, reliable path in a controlled setting.
- Provide ordered steps with visible results early and often.
- Show expected output, checks, and signs of trouble.
- Minimize explanation to what keeps the learner moving.
- Avoid alternatives, production variability, exhaustive options, and early decisions.
- End with a clear completed outcome that a real learner can test.

### How-To Guide

Write practical directions for a competent user completing real work.

- Name the real-world goal or problem.
- State prerequisites, assumptions, and useful starting points.
- Use action-focused steps ordered by how people work.
- Include branches, warnings, checks, and verification where reality branches.
- Keep teaching, background, and reference detail short.
- Link to reference for full options and explanation for background.
- Start and end at useful work boundaries; do not force an end-to-end lesson shape.

### Reference

Write neutral factual description of the machinery.

- Describe APIs, commands, options, fields, parameters, defaults, constraints, return values, errors, behavior, and limits.
- Use consistent schemas, tables, signatures, and predictable headings.
- Mirror product/API/system structure where it helps consultation.
- Prioritize accuracy, precision, consistency, completeness, and currency.
- Include warnings and constraints.
- Use concise examples only to clarify facts or correct usage.
- Avoid task workflows, persuasion, design rationale, broad concept discussion, and teaching sequences.

### Explanation

Write bounded discussion that builds understanding.

- Answer a clear why/about/concepts question.
- Provide context, reasons, design decisions, constraints, history, implications, tradeoffs, alternatives, and comparisons.
- Connect concepts into a mental model.
- Allow perspective and judgement where helpful.
- Keep steps, commands, and exact factual tables brief and illustrative.
- Link to how-to guides for action and reference for exact facts.
- Avoid becoming an unbounded essay, task guide, or hidden reference manual.

## Boundary Rules

Tutorial vs how-to:

- Distinguish by study vs work, not beginner vs advanced.
- Use tutorials when the author controls the path for learner safety and confidence.
- Use how-to guides when the reader has a real task and may need branches or judgement.
- Keep production variability out of tutorials unless that variability is the lesson.
- Keep basic teaching out of how-to guides unless it is immediately necessary and brief.

Reference vs explanation:

- Use reference for exact facts consulted during work.
- Use explanation for context, reasons, tradeoffs, and conceptual connections.
- Keep lists, schemas, signatures, and option tables in reference.
- Keep rationale, alternatives, and perspective in explanation.
- Do not hide critical commands or exact facts inside explanation.
- Do not turn reference examples into tutorials or essays.

Action vs cognition:

- Treat steps, workflows, checks, commands, and troubleshooting procedures as action unless merely illustrative.
- Treat definitions, constraints, schemas, concepts, reasons, and tradeoffs as cognition.
- If action and cognition alternate repeatedly, choose the reader's immediate need and move or link the rest.

User need vs product structure:

- Shape tutorials around the learner's journey.
- Shape how-to guides around human goals, not product controls.
- Shape explanation around coherent why/about topics.
- Shape reference around the machinery when product structure supports lookup.

## Mixed Docs And Hierarchies

- For mixed requests, split output into Diataxis-aligned sections or ask which need is primary only if the split changes the deliverable.
- Keep a page in one dominant mode, then link to sibling material for secondary needs.
- Treat README files and landing pages as routing surfaces when appropriate: brief overview, a clear next action, and links into tutorial/how-to/reference/explanation material.
- Treat troubleshooting as usually how-to; put error-code tables in reference and root-cause discussion in explanation when they grow beyond support notes.
- Treat API documentation as usually reference, with separate tutorials, task guides, and explanations when the user needs a complete docs set.
- Use role, platform, product area, deployment environment, or lifecycle as the top hierarchy when that better matches how users navigate. Preserve mode clarity inside that hierarchy.
- Do not create empty Tutorial / How-to / Reference / Explanation folders before real content and user paths justify them.
- Follow local documentation conventions unless they obscure user needs. Suggest page renames such as "How to..." or "About..." when they improve findability, not as a rule.

## Review Practice

Review functional quality separately from Diataxis fit.

- Functional checks: accuracy, completeness, consistency, precision, currency, technical correctness, and usefulness.
- Diataxis checks: primary user need, mode consistency, flow, anticipation, misplaced material, and whether anything interrupts the reader's current purpose.
- For findings, prioritize by user impact: blocking, confusing, or polish. Use explicit severity labels only when the user asks for a formal review.
- Recommend concrete moves: split, move, link, shorten, retitle, rewrite, or add missing checks/facts/context.

## Anti-Patterns

- Beginner how-to mislabeled as tutorial.
- Advanced tutorial mislabeled as how-to.
- How-to organized around product controls instead of user goals.
- Tutorial overloaded with options, abstractions, production branches, or long explanation.
- Reference polluted by task workflows, conceptual essays, opinions, or marketing.
- Explanation hiding critical procedures or exact lookup facts.
- Generated API reference treated as a complete documentation set.
- Mixed pages left mixed merely because all material shares a topic.
- Completeness pursued at the expense of flow in tutorials and how-to guides.
- Large information-architecture rewrites attempted before small high-confidence improvements.

## Templates

Read `references/templates.md` when drafting new documentation from scratch, restructuring material into new pages, or when the user asks for examples, templates, or skeletons. Adapt the skeletons to local conventions and remove placeholders.
