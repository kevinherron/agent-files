---
name: writing-commit-messages
description: Create Git commits with clear messages when committing is requested or authorized by the task. A message-only request produces a draft without committing.
---
# Writing commit messages

Inspect the staged and unstaged diff, working-tree status, and recent commit style.
Use conversation context for intent and the diff for delivered scope.

## Authorization and scope

An explicit request to commit authorizes staging and committing the requested changes.
A governing workflow may also authorize commits. Carry that authorization forward without
an extra approval round. A request only to draft a message does not authorize a commit;
a request only to implement changes does not authorize one unless the workflow says so.

When the intended scope is clear, prepare the commit internally and execute it. Ask only
when ownership or scope is materially ambiguous, an applicable approval requirement
remains unsatisfied, or the action would exceed existing authorization. Prepare the
proposed files and messages before asking. Leave unrelated user changes untouched.

## Commit shape

Group one coherent change with the tests and documentation that support it. Split commits
when they serve independent purposes, not merely because files have different types.
Stage explicit paths or selected hunks; inspect the staged diff before committing.
Do not stage unrelated hunks in a partially shared file. Exclude credentials and secrets.

Match the repository's conventions. Otherwise use:

```text
<Short imperative summary>

<Optional explanation of motivation, constraints, or non-obvious trade-offs>
```

Aim for a summary around 50 characters, up to 72 when useful. Capitalize the first word
and omit a trailing period unless repository style differs. Omit the body when the
summary is sufficient. Explain the change's intent rather than listing files.

Pass the message through a temporary file or quoted heredoc so literal text cannot be
interpreted by the shell. After committing, verify the resulting commit and working-tree
state. Report the hash and summary. Do not create an empty commit or push unless requested
or authorized by the governing workflow.
