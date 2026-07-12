---
name: writing-commit-messages
description: "Create well-crafted git commits from session changes or staged work. Use this skill whenever the user asks to commit changes, says 'commit this', 'commit my changes', '/commit', 'create a commit', 'write a commit message', or any request to turn code changes into git commits. Also use it when an autonomous goal or implementation workflow includes creating a commit. Direct user activation is approval-gated; incidental activation by an already-authorized workflow is not."
---
Create git commits with clear, well-structured messages.

The diff is always your primary source of truth.
When conversation history is available (e.g., you worked on the changes in this
session), use it to understand intent — but you’ll often be committing from a fresh
session with no history, or the history may only cover part of the changes.
In those cases, read the diff carefully and let the code speak for itself.

## Approval mode

Determine the activation mode before beginning:

- **Explicit activation:** The user directly invokes this skill or asks to create a
  commit as the primary action. Present the commit plan and wait for explicit approval
  before staging or committing.
- **Incidental activation:** An autonomous goal, implementation workflow, or other
  higher-level process invokes this skill to perform a commit that the process already
  authorizes. Do not add a redundant approval checkpoint. Inspect the changes, plan the
  commit internally, and execute it as part of that workflow.

Treat an invocation as incidental only when the governing task already authorizes the
commit. A request to implement changes does not, by itself, grant permission to commit
unless the surrounding workflow establishes that behavior. When the distinction is
genuinely ambiguous, use explicit activation mode.

## Process

1. **Understand what changed:**
   - Run `git status` to see the current state
   - Run `git diff` (both staged and unstaged) to see actual modifications
   - Run `git log --oneline -5` to learn the repo’s commit style
   - If conversation history is available, use it for additional context on intent

2. **Plan the commit(s):**
   - Decide whether changes should be one commit or multiple.
     Split when changes serve genuinely different purposes (a refactor + a new feature,
     a bug fix + a test addition).
     Keep together when changes form one coherent unit.
   - Group related files together
   - Draft each commit message using the format below

3. **Handle the commit plan according to the approval mode:**
   - For explicit activation, show for each planned commit:
     - The files to be staged
     - The full commit message
   - For explicit activation, ask: “I plan to create N commit(s) with these changes.
     Shall I proceed?”
   - For explicit activation, **do not execute until the user explicitly approves.**
     If the user requests changes, revise the plan and ask for approval again — every
     revision resets the approval.
   - For incidental activation, keep the plan internal unless the governing workflow
     requests a progress summary. Do not present it as an approval gate or pause for
     confirmation. Continue directly to execution.

4. **Execute after the required authorization:**
   - In explicit activation mode, execute only after explicit user approval
   - In incidental activation mode, the governing workflow's authorization is
     sufficient
   - Stage specific files with `git add <file>` (never use `-A` or `.`)
   - Create commits using a HEREDOC for the message to preserve formatting
   - Show the result with `git log --oneline -n N`

## Commit message format

```
<summary line>

<optional body>
```

**Summary line:**
- Imperative mood ("Add user auth" not “Added” or “Adds”)
- Keep it short — aim for 50 characters, 72 max.
  Brevity forces clarity.
- Capitalize the first word
- No trailing period
- Describe the change at the intent level, not the file level ("Add retry logic for
  flaky API calls" not “Update api_client.py”)

**Body (when the summary alone isn’t enough):**
- Separated from the summary by a blank line
- Explain the *motivation* — the “why” behind the change
- The diff already shows the “what”, so don’t restate it
- Mention trade-offs, constraints, or decisions that aren’t obvious from the code
- Skip the body entirely for self-evident changes

**Adapting to repo style:**
- If the repo uses conventional commits (`feat:`, `fix:`, etc.), follow that
- If the repo uses ticket prefixes (`PROJ-123:`), follow that
- Match whatever pattern `git log` reveals — consistency matters more than any one style

## Guidelines

- Write messages as if the user wrote them — match the voice of the repo
- Keep commits atomic: one logical change per commit
- Never commit files that look like secrets (.env, credentials, API keys)
- Do not push to remote unless the user explicitly asks
- If there are no changes to commit, say so — don’t create empty commits
