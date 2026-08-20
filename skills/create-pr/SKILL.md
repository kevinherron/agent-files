---
name: create-pr
description: Use when the user asks to create or open a pull request (PR).
---
# Create PR

PR titles should be concise and descriptive.
A good PR title is human-readable and explains why the change matters.

Open the description with a simple explanation of the modification, feature, or problem being solved, then briefly explain the approach.
Do not lead with an implementation inventory.
Do not include counts of files, tests added, or lines of code changed.
Focus on the problem being solved and the approach taken.

Tell the story in prose, not in headings.
If the body uses section headings, keep them to a few plain structural labels, never sentences that carry the narrative or one heading per fix or finding.

Write the body as flowing prose. GitHub soft-wraps Markdown, so do not hard-wrap paragraphs to a fixed column the way commit messages are wrapped.

Include relevant verification actually performed and any material risks, limitations, rollout notes, or follow-up work. Never claim tests or checks that were not run or observed.

## Gathering context

Determine the base branch before reconstructing the change. Prefer the user's explicit choice, then stacked or maintenance branch context, branch metadata, and linked issue context. Use the repository default when there is no contrary signal. Ask only when multiple plausible bases would materially change the PR.

Fetch the selected base from its remote, then use the remote-tracking ref for context, such as `git log <base-remote>/<base>..HEAD` and `git diff <base-remote>/<base>...HEAD`. Review the commit range and diff for unrelated or unexpected work before publishing.

Combine sources rather than relying on one. The user's original prompt explains why, commits show intended work, the diff shows what actually changed, and a linked issue often carries background the prompt assumed. Treat the diff as authoritative for delivered scope, not rationale. Reconcile the sources and flag material discrepancies to the user before creating the PR. Include a discrepancy in the body only when reviewers need to know about it.

Without the original prompt, reconstruct the rationale from the commits, issue, and diff. If it still is not clear, ask rather than inventing a rationale or merely narrating the code.

## Creating the PR

Prefer the `gh` CLI when it is available and authenticated for the repository host (`gh auth status`).

1. Inspect the current branch, working tree, and remotes. Require a named branch. If uncommitted changes appear to belong in the requested PR, stop and explain that the PR cannot include them yet. Do not assume a dirty working tree is represented by `HEAD`.

2. Check the target repository for an existing open PR from the current branch. Prefer machine-readable output, for example:

   ```text
   gh pr list --state open --head <branch> --json url,number,title,baseRefName,isDraft
   ```

   Add `--repo <owner/repo>` when the target repository is not the one inferred by `gh`. If an existing PR already satisfies the request, report its URL instead of opening a duplicate. If it needs changes, explain them and ask before updating the existing PR.

3. Resolve the push remote from the branch upstream and repository remotes. Push the current `HEAD` so the hosted branch includes all local commits. Add `-u` only when the branch has no upstream. Do not assume the push remote is named `origin`. Stop on a rejected push, and never force-push unless the user explicitly authorizes it.

4. Write the body to a temporary file outside the worktree, then create the PR with `--body-file` so formatting survives:

   ```
   gh pr create --base <base> --title "<title>" --body-file <path>
   ```

   Add `--head <owner>:<branch>` when a fork or nonstandard remote requires it. Add `--draft` when the user requests a draft or the context clearly identifies unfinished work. Remove the temporary body file after the command completes.

5. Read the PR back with `gh pr view --json url,title,baseRefName,headRefName,isDraft`. Verify the important fields, then report the resulting URL.

If `gh` is unavailable or unauthenticated, use another already authenticated GitHub integration when one is available. Otherwise explain the limitation and offer to push the branch and provide the compare URL, or to use the GitHub API after authentication. Do not silently choose a materially different workflow.
