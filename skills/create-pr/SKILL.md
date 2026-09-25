---
name: create-pr
description: "Create or update a GitHub pull request for the requested changes."
---
# Create PR

## Writing the description

Write for an experienced engineer who has not followed the conversation. The description should explain the change without requiring the reviewer to reconstruct its purpose from the diff or linked issues.

Lead with the problem or intended improvement. Explain:

- What situation triggers the relevant behavior.
- What happened before.
- What happens after.
- Why the change is needed.

Use concrete inputs, outputs, errors, or user actions when they make the difference easier to understand. Prefer plain terms; connect necessary technical terms to the behavior they describe.

Distinguish behavior changes from added verification, refactoring, and already-existing behavior. For a test-only change, explain what was previously unverified and what the new tests establish. For a refactor, explain what responsibility or flow changes and why that helps.

Do not lead with an implementation inventory or counts of files, tests added, or changed lines. Mention files and symbols when they help the reviewer locate or understand an important mechanism.

Scale the explanation to the change. A small PR may need only one or two paragraphs. A larger PR may benefit from a before-and-after table and a few plain section headings. Do not force every PR into the same template.

Use the smallest visual that makes the change clearer:

- A before-and-after table for several distinct behavior changes.
- A short diff for changed code shape or output.
- Pseudocode for a rule or algorithm.
- A small Mermaid diagram for control flow or component interaction.

Place each visual beside its explanation. Keep examples faithful to the implementation and label simplified or illustrative snippets. Use formats that render directly in the PR description.

Explain what verification establishes, including material limits, risks, and rollout considerations. Separate completed fixes from deferred work. Put detailed commands, versions, counts, and evidence links after the explanation of the change. Never claim tests or checks that were not run or observed.

Keep titles concise and descriptive. Use flowing prose without hard-wrapped paragraphs. Headings should organize the explanation, not carry it.

## Gathering context

Determine the base branch before reconstructing the change. Prefer the user's explicit choice, then stacked or maintenance branch context, branch metadata, and linked issue context. Use the repository default when there is no contrary signal. Ask only when multiple plausible bases would materially change the PR.

Fetch the selected base from its remote, then use the remote-tracking ref for context, such as `git log <base-remote>/<base>..HEAD` and `git diff <base-remote>/<base>...HEAD`. Review the commit range and diff for unrelated or unexpected work before publishing.

Combine sources rather than relying on one. The user's original prompt explains why, commits show intended work, the diff shows what actually changed, and a linked issue often carries background the prompt assumed. Treat the diff as authoritative for delivered scope, not rationale. Reconcile the sources and flag material discrepancies to the user before creating the PR. Include a discrepancy in the body only when reviewers need to know about it.

Without the original prompt, reconstruct the rationale from the commits, issue, and diff. If it still is not clear, ask rather than inventing a rationale or merely narrating the code.

## Creating the PR

Prefer the `gh` CLI when it is available and authenticated for the repository host (`gh auth status`).

1. Inspect the current branch, working tree, and remotes. Require a named branch. If uncommitted changes belong in the requested PR and the task authorizes committing them, inspect and commit that scope before publishing. Otherwise prepare the PR context and ask only for the missing scope or commit authorization. Leave unrelated changes alone. Do not assume a dirty working tree is represented by `HEAD`.

2. Check the target repository for an existing open PR from the current branch. Prefer machine-readable output, for example:

   ```text
   gh pr list --state open --head <branch> --json url,number,title,baseRefName,isDraft
   ```

   Add `--repo <owner/repo>` when the target repository is not the one inferred by `gh`. If an existing PR already satisfies the request, report its URL instead of opening a duplicate. If it needs changes within the requested scope, update it when existing authorization covers those changes. Ask only about material scope differences or missing authorization.

3. Resolve the push remote from the branch upstream and repository remotes. Push the current `HEAD` so the hosted branch includes all local commits. Add `-u` only when the branch has no upstream. Do not assume the push remote is named `origin`. Stop on a rejected push, and never force-push unless the user explicitly authorizes it.

4. Write the body to a temporary file outside the worktree. Before publishing, read the draft as someone unfamiliar with the task. Can they explain what changed and why, distinguish fixes from tests, and identify what remains unresolved? Replace vague claims with concrete examples before publishing. Then create the PR with `--body-file` so formatting survives:

   ```
   gh pr create --base <base> --title "<title>" --body-file <path>
   ```

   Add `--head <owner>:<branch>` when a fork or nonstandard remote requires it. Add `--draft` when the user requests a draft or the context clearly identifies unfinished work. Remove the temporary body file after the command completes.

5. Read the PR back with `gh pr view --json url,title,body,baseRefName,headRefName,isDraft`. Verify the published description as well as the PR metadata. Check that tables, code fences, diagrams, and links survived correctly, then report the resulting URL.

If `gh` is unavailable or unauthenticated, use another already authenticated GitHub integration when one is available. Otherwise explain the limitation and offer to push the branch and provide the compare URL, or to use the GitHub API after authentication. Do not silently choose a materially different workflow.
