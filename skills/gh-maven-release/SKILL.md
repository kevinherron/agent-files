---
name: gh-maven-release
description: Run, monitor, resume, and recover release-branch-based Maven releases published through GitHub Releases and GitHub Actions. Use when Codex needs to release a Maven project by setting a non-SNAPSHOT version, creating a release branch and GitHub tag/release, monitoring the deployment workflow, advancing to the next SNAPSHOT, opening the merge-back PR, diagnosing a failed release, or safely retrying after deleting a failed GitHub release and tag.
---

# GitHub Maven Release

Release a Maven reactor through a GitHub Release-triggered workflow while preserving enough state
to diagnose or resume every phase. Treat artifact publication as irreversible even when GitHub tags
and releases remain deletable.

## Establish intent and repository rules

1. Read repository agent instructions and release documentation completely before acting.
2. Inspect the current branch, worktree, remotes, Maven coordinates and version, recent release
   branches/tags, GitHub release workflow, and publishing profile.
3. Determine the target version, release branch, tag, base branch, and next development version.
   Use `release/<version>` and `v<version>` only when consistent with repository convention.
4. Require an explicit next development version when patch-versus-minor intent is ambiguous. Do not
   assume that `0.5.0` implies either `0.5.1-SNAPSHOT` or `0.6.0-SNAPSHOT`.
5. Distinguish **prepare** from **publish**. Preparing may create a branch, version commit, pushed
   tag, or draft release as requested. Publishing a GitHub Release may deploy immutable artifacts;
   do it only when the user explicitly requests an actual release.
6. Obey repository-specific build delegation requirements. Never bypass a failing check.

Verify prerequisites with `git`, `mvn --version`, `gh auth status`, and `gh repo view`. Stop if the
worktree contains unrelated changes, the base branch is not synchronized, credentials are missing,
or the target release/tag/version already exists in an unexplained state.

## Record resumable state

Initialize state after resolving the release inputs:

```bash
python3 <skill-dir>/scripts/release_state.py init \
  --repository OWNER/REPO \
  --base-branch main \
  --release-branch release/1.2.3 \
  --version 1.2.3 \
  --next-version 1.2.4-SNAPSHOT \
  --tag v1.2.3
```

Run `show` before resuming an existing release. Use `set KEY VALUE` immediately after each external
mutation or durable Git operation. The state lives in the Git common directory, not the worktree.
Archive it after the merge-back PR is created:

```bash
python3 <skill-dir>/scripts/release_state.py archive
```

Use keys defined by `python3 <skill-dir>/scripts/release_state.py set --help`. Never record secrets.

## Preflight the release

1. Fetch and prune normally; do not rewrite public history. Confirm local base, remote base, and the
   intended starting SHA.
2. Confirm the reactor is currently on a SNAPSHOT version and all internal parent/module versions
   are aligned.
3. Inspect `.github/workflows` to identify the exact trigger and deploy job. Record whether it reacts
   to `release.published`, tag pushes, `workflow_dispatch`, or another event. Detect duplicate
   triggers that could deploy the same coordinates twice.
4. Inspect the release profile, signing, Maven Central publishing plugin, source/javadoc artifacts,
   SCM coordinates, and credentials expected by Actions.
5. Run the repository's complete prescribed verification on the clean base branch.
6. Inspect active publishing runs. Wait for or resolve an in-flight snapshot/release deployment from
   the same repository before publishing a release candidate.
7. Save `base_sha`, `workflow_file`, and `workflow_event`, then set phase `preflight-complete`.

Do not invoke `release:perform` when GitHub Actions already deploys the release; this risks duplicate
publication.

## Create the release candidate

Create the release branch from the recorded base SHA. Set the reactor version with the repository's
preferred mechanism, normally:

```bash
mvn -B versions:set \
  -DnewVersion="$VERSION" \
  -DprocessAllModules=true \
  -DgenerateBackupPoms=false
```

Then:

1. Inspect the diff. Accept only intended Maven version changes; remove no unrelated files.
2. Run the full prescribed verification at the release version.
3. Commit with the repository's commit-message rules, normally `Set version to <version>`.
4. Record `version_commit_sha` and `release_sha`.
5. Push the release branch without force and record phase `candidate-pushed`.
6. Re-read the remote branch SHA, require it to equal `release_sha`, and record it as
   `release_branch_remote_sha`.

## Create and review the draft release

Target the immutable recorded commit SHA rather than a movable branch name:

```bash
gh release create "$TAG" \
  --repo "$REPOSITORY" \
  --target "$RELEASE_SHA" \
  --draft \
  --generate-notes \
  --title "$TAG" \
  --fail-on-no-commits
```

Record `release_url`, `release_id`, and phase `draft-created`. Fetch tags and verify that the remote
tag resolves to `release_sha` if GitHub has materialized it; record it as `tag_sha`. Review generated
notes against the actual commits and user-facing changes. Correct omissions or misleading entries
before publishing.

Pause here unless the user has explicitly authorized publishing the release. Clearly state that
publishing will trigger the identified deployment workflow.

## Publish and identify the exact workflow run

Publish the reviewed draft with `gh release edit "$TAG" --repo "$REPOSITORY" --draft=false`.
Immediately record the publication timestamp and phase `release-published`.

Poll `gh run list` for a run matching all available evidence:

- the workflow file or workflow name identified during preflight;
- the expected event (`release`, `push`, or explicit dispatch);
- `headSha == release_sha` when GitHub supplies it;
- creation at or after the recorded publication timestamp.

Do not watch the merely latest repository run. If no run appears, inspect trigger filters and the
release event payload rather than publishing again. Record `workflow_run_id` and `workflow_url`, then
run:

```bash
gh run watch "$WORKFLOW_RUN_ID" --repo "$REPOSITORY" --compact --exit-status
```

Keep the user updated during long runs. On success, inspect the run jobs and confirm the deployment
step actually ran rather than being skipped. Record phase `deployment-succeeded`.

## Complete a successful release

1. Optionally verify the released coordinates in the configured repository, allowing for indexing
   delay. Do not treat delayed search indexing as a failed deployment when Actions and the publishing
   service report success.
2. On the release branch, set the explicitly chosen next SNAPSHOT across the reactor.
3. Inspect the diff, run appropriate verification, and commit `Set version to <next-version>`.
4. Push the release branch normally and record `snapshot_commit_sha`.
5. Open a non-draft PR from the release branch to the base branch unless one already exists. Explain
   that it advances development to the next SNAPSHOT and includes any release-only fixes.
6. Record `pr_url`, set phase `merge-back-pr-opened`, report the release, deployment run, coordinates,
   and PR, then archive state.

Do not merge the PR unless the user asks.

## Recover a failed run

Read [references/recovery.md](references/recovery.md) completely before taking recovery action.
First collect failed logs with `gh run view <id> --log-failed` and determine whether any upload,
staging, validation, publish, close, or release action reached the artifact repository.

Classify the failure:

- **Proven pre-deployment:** the deploy/publish step never started. The version may be safely retried
  after explicit approval to delete/recreate GitHub state.
- **Deployment possibly started:** treat the version as potentially consumed. Inspect Maven Central
  or the configured publishing service before deleting anything or reusing the version.
- **Deployment succeeded but a later step failed:** never retry the same deploy. Preserve the release
  and repair only the downstream step, or use a new version if another artifact publication is
  required.
- **Ambiguous:** stop with evidence and exact safe next checks. Never infer safety from a red workflow
  conclusion alone.

Deleting a published release/tag and rewriting a pushed release branch are destructive operations.
Require explicit approval for the resolved repository, tag, release, branch, and expected remote
SHA. Create a backup ref first and use `--force-with-lease` with the exact expected SHA when a retry
must reorder the release-version commit after fixes. Never force-push the base branch.

## Report

Report the release/tag/branch and exact SHAs, Maven coordinates, verification results, GitHub Release
URL, Actions run URL and conclusion, next-SNAPSHOT commit, merge-back PR, and any remaining manual
checks. If blocked, report the current state phase and the exact non-destructive command that resumes
diagnosis.
