---
name: create-pr
description: Use when the user asks to create or open a pull request (PR).
---
# Create PR

PR titles should be concise and descriptive.
A good PR title is human-readable and explains why the change matters.

Open the description with a simple explanation of the problem, then briefly explain the
solution. Do not lead with an implementation inventory.
Do not include counts of files, tests added, or lines of code changed.
Instead, focus on the problem being solved and the approach taken.

Tell the story in prose, not in headings.
If the body uses section headings, keep them to a few plain structural labels
- never sentences that carry the narrative, and never one heading per fix or finding.

## Gathering context

Combine sources rather than relying on one: the user’s original prompt says why, the
commits (`git log <base>..HEAD`) say what was intended, the diff
(`git diff <base>...HEAD`) says what actually happened, and a linked issue often carries
background the prompt assumed.
Where they disagree, trust the diff and flag the discrepancy.

Without the original prompt — branch picked up later, session resumed, work handed off —
reconstruct the “why” from the commits, issue, and diff.
If it still isn’t clear, ask rather than inventing a rationale or narrating what the
code does.

## Creating the PR

Always prefer the `gh` CLI when it is available and authenticated (`gh auth status`).

1. Check for an existing PR: `gh pr list --head "$(git branch --show-current)"`. If one
   exists, report its URL and ask whether to update it rather than opening a second PR.

2. Confirm the base branch.
   Do not assume the repo default — a stacked or maintenance branch usually targets
   something else.

3. Push the branch with an upstream if it has none: `git push -u origin HEAD`.
   `gh pr create` fails without it.

4. Write the body to a file, then create the PR with `--body-file` so formatting
   survives:

   ```
   gh pr create --base <base> --title "<title>" --body-file <path>
   ```

   Add `--draft` when the work isn’t ready for review.

5. Report the resulting PR URL.

If `gh` is unavailable or unauthenticated, say so and offer the alternatives — pushing
the branch and giving the user the compare URL, or using the GitHub API directly —
rather than silently picking one.
