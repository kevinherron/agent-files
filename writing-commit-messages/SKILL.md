---
name: writing-commit-messages
description: "Create well-crafted git commits from session changes or staged work. Use this skill whenever the user asks to commit changes, says 'commit this', 'commit my changes', '/commit', 'create a commit', 'write a commit message', or any request to turn code changes into git commits. Also triggers when the user finishes a task and wants to commit the results, or says 'let's commit', 'save this', 'wrap this up with a commit', or similar."
---
Create git commits with clear, well-structured messages.

The diff is always your primary source of truth.
When conversation history is available (e.g., you worked on the changes in this
session), use it to understand intent — but you’ll often be committing from a fresh
session with no history, or the history may only cover part of the changes.
In those cases, read the diff carefully and let the code speak for itself.

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

3. **Present your plan and wait for approval:**
   - For each planned commit, show:
     - The files to be staged
     - The full commit message
   - Ask: “I plan to create N commit(s) with these changes.
     Shall I proceed?”
   - **Do not execute until the user explicitly approves.** If the user requests
     changes, revise the plan and ask for approval again — every revision resets the
     approval.

4. **Execute only after explicit approval:**
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
