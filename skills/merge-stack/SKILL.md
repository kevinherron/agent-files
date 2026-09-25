---
name: merge-stack
description: Merge an entire GitHub PR stack with a derived stack-wide merge commit title and body, accepting any member PR number or URL. Also draft the message without merging when requested.
---

Accept any member PR as the identifier for the entire stack, including layers above it. Default to a merge commit. A request only to draft a message or discuss capability does not authorize a merge. An explicit `merge-stack <PR>` invocation requests the full workflow. Honor any existing requirement to preview or approve the message; otherwise show the concrete scope and message before proceeding within the user's authorization, without inventing an extra confirmation gate.

## Resolve and summarize

1. Resolve owner/repository from the PR URL or current repository for a bare PR number. Treat bare numbers as PR numbers, never stack numbers.
2. Read `gh api repos/OWNER/REPO/pulls/PR`, then use its `stack.number` with `gh api repos/OWNER/REPO/stacks/STACK_NUMBER`. Resolve all unmerged members and the top PR from their branch dependencies and stack order. Record the destination branch and each member's head SHA. If membership is absent or ambiguous, investigate read-only and ask for scope if necessary; do not silently merge a single PR or create a stack.
3. Read all included PR descriptions and inspect their diffs or the combined diff against the actual stack base. Verify local revisions match remote heads before relying on local Git. The target may be an integration or release branch. Exclude unrelated target-branch changes.
4. Derive one imperative title, preferably under 72 characters, covering the shared purpose. Write a compact body explaining behavior, motivation, and material constraints. Include constituent PR numbers. Avoid file inventories, copied verification logs, and unsupported test claims. In draft-only mode return title and body in separate plain-text code blocks and stop.

## Merge through gh api

The installed `gh stack merge` checked on 2026-09-05 has no custom title/body flags. Use GitHub's asynchronous merge endpoint through `gh api`; the legacy synchronous merge endpoint does not support stacks. Calling the asynchronous endpoint on a middle PR only merges through that layer, so submit the resolved top PR to merge the entire stack.

Before submission, show the included PRs, destination, and exact title/body. Inspect merge readiness and required checks across the stack. Re-read membership and head SHAs; if they changed, refresh the diff, message, and preview. Do not bypass protections or silently rebase, push, edit PR metadata, or delete branches. No local build is needed solely to derive a message; honor applicable repository verification requirements for an actual merge.

Serialize this payload to a temporary JSON file, preserving actual newlines and avoiding shell interpolation of message text:

```json
{
  "commit_title": "Derived title",
  "commit_message": "Derived body",
  "sha": "TOP_PR_HEAD_SHA",
  "merge_method": "merge",
  "merge_action": "default"
}
```

Submit once:

```sh
gh api --method PUT repos/OWNER/REPO/pulls/TOP_PR/merge-async \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2026-03-10' \
  --input /path/to/payload.json
```

GitHub evaluates protections asynchronously. An accepted request is not proof of a merge. Retain the returned UUID and poll `GET repos/OWNER/REPO/pulls/TOP_PR/merge-async/UUID`. Use bounded polling with progress updates; if still pending after five minutes, report the pending or queued state and UUID without claiming completion. On a conflict indicating an existing request, inspect it rather than submitting again or assuming its message matches. After an uncertain network outcome, check remote state before retrying. On a terminal failure, report the reason and stop rather than changing merge options or bypassing rules.

After success, read back the resulting commit's title/body and parents, and confirm every intended PR is merged. Report the commit link and any discrepancy. Do not rewrite the target branch if the server produced an unexpected message.

## Merge message context

The message describes the whole stack, not merely its top PR. Preserving original commits does not remove the need for a stack-wide merge message. Observed precedent: eclipse-milo/milo commit `2cb1643de14a0ad3e656fb8d5c4cc20f83d50136` landed a two-PR stack with one two-parent merge commit and three ordinary commits, with no intermediate merge commit. Do not reopen merge semantics unless asked or contrary concrete evidence appears. This precedent is not a guarantee for every merge method or future implementation.

API reference: https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request-asynchronously
