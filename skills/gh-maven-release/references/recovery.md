# Failed release recovery

Read this playbook only after a release workflow fails or a prior release attempt must be resumed.

## Contents

- [Freeze and gather evidence](#freeze-and-gather-evidence)
- [Classify artifact publication](#classify-artifact-publication)
- [Recover a proven pre-deployment failure](#recover-a-proven-pre-deployment-failure)
- [Keep the version commit after fixes](#keep-the-version-commit-after-fixes)
- [Handle possible or completed publication](#handle-possible-or-completed-publication)
- [Resume after interruption](#resume-after-interruption)

## Freeze and gather evidence

Do not delete the release, tag, branch, workflow run, or publishing-service deployment yet.

1. Show recorded state and verify it against live GitHub state.
2. Capture `gh release view <tag> --json` data, the remote tag SHA, release-branch SHA, run summary,
   job/step conclusions, and failed logs.
3. Read the workflow at the released SHA, not only the current default branch. Identify the first
   command capable of contacting the artifact repository.
4. Record phase `failure-investigation` and the failed run ID.

Useful commands include:

```bash
gh run view "$RUN_ID" --repo "$REPOSITORY" --json headSha,event,status,conclusion,url,jobs
gh run view "$RUN_ID" --repo "$REPOSITORY" --log-failed
gh release view "$TAG" --repo "$REPOSITORY" --json id,isDraft,publishedAt,targetCommitish,url
git ls-remote --refs origin "refs/heads/$RELEASE_BRANCH" "refs/tags/$TAG"
git show "$RELEASE_SHA:.github/workflows/<release-workflow>.yml"
```

## Classify artifact publication

Use workflow steps and logs, not the overall conclusion.

### Proven pre-deployment

Classify as proven pre-deployment only if the repository-contacting deploy/publish step did not
start. Examples include compilation, formatting, tests, packaging, signing, or setup failing before
`mvn deploy` or an upload action begins.

### Possibly started

Classify as possibly started if `mvn deploy`, Central Portal upload, staging, validation, close,
publish, or equivalent began—even if it returned an error. Check the publishing service using the
deployment identifier from logs or its authenticated UI/API. A Maven Central search result is useful
positive evidence but weak negative evidence because synchronization and indexing can lag.

Do not assume that deleting a GitHub tag or release makes Maven coordinates reusable. Artifact
repositories generally treat released coordinates as immutable.

### Completed publication

If the artifact repository accepted or published the version, preserve the tag and release. Retry
only an idempotent downstream task if the workflow supports it. Otherwise fix forward with a new
version; never overwrite released coordinates.

## Recover a proven pre-deployment failure

Before destructive actions, present:

- repository and release URL;
- tag and its exact SHA;
- release branch and its exact remote SHA;
- evidence that deployment never started;
- the release/tag deletion and branch-rewrite operations proposed.

Proceed only after explicit approval. Create recoverable refs before deletion:

```bash
git fetch origin "$RELEASE_BRANCH" --tags
git branch "backup/$TAG-failed" "$RELEASE_SHA"
```

Use `gh release delete <tag> --cleanup-tag --yes` only after confirming its semantics with
`gh release delete --help` for the installed CLI. If the release is immutable or GitHub refuses the
operation, stop. Delete a local tag only after preserving the backup ref.

Diagnose and fix the actual failure on the release branch. Run the failing check and then the full
prescribed verification. Do not weaken, skip, or bypass the check.

## Keep the version commit after fixes

Prefer placing fixes before `Set version to <version>` so the tagged release commit remains a clear
version boundary. Reordering a pushed release branch rewrites only that release branch and requires
explicit approval.

Before rewriting:

1. Verify the recorded version commit is an ancestor of the current release branch.
2. Verify the remote branch still equals the expected recorded SHA.
3. Preserve the current tip under `backup/<tag>-failed`.
4. Ensure the base branch is never the rewrite target.

For a linear history containing one version commit followed by fix commits, a deterministic pattern
is to move the fix commits onto the version commit's parent and then cherry-pick the version commit:

```bash
VERSION_COMMIT=<recorded-version-commit>
EXPECTED_REMOTE=<recorded-release-branch-sha>
git rebase --onto "${VERSION_COMMIT}^" "$VERSION_COMMIT" "$RELEASE_BRANCH"
git cherry-pick "$VERSION_COMMIT"
```

Resolve conflicts by preserving the fixes and setting every reactor module to the release version.
Run full verification, record the new version and release SHAs, then push with a fully qualified,
exact lease:

```bash
git push \
  --force-with-lease="refs/heads/$RELEASE_BRANCH:$EXPECTED_REMOTE" \
  origin "HEAD:refs/heads/$RELEASE_BRANCH"
```

Never use an unqualified `--force`, never omit the expected lease SHA, and never rewrite `main` or
the repository's base branch. Recreate the draft release at the new recorded release SHA, review its
notes, and publish only with renewed user authorization.

If the history is nonlinear, contains multiple version commits, or fixes touch the same POM version
lines, do not apply the pattern mechanically. Construct and show a commit graph, choose a safe plan,
and preserve authorship.

## Handle possible or completed publication

If publication may have started:

1. Extract any deployment/staging identifier from logs.
2. Inspect the authenticated publishing-service state.
3. Check the exact group ID, artifact IDs, version, classifiers, and module set.
4. Decide whether the deployment can be resumed, must be dropped, has already published, or has
   permanently consumed the version.

Do not drop a publishing-service deployment, delete GitHub state, or choose a replacement version
without explicit user approval. If coordinates were published, use the next appropriate version for
artifact fixes and document the failed downstream automation separately. Ask for both the replacement
release version and its following development version when the originally planned next SNAPSHOT would
conflict with the replacement release.

## Resume after interruption

Run the state utility's `show` command, then verify every recorded mutable reference against GitHub.
Trust immutable SHAs over branch names. Continue from the earliest phase whose postconditions are
not yet satisfied; do not repeat completed external mutations.

If state is missing, reconstruct it read-only from Git history, remote refs, GitHub Releases, and
Actions. Initialize a new state file only after presenting the reconstructed values. If competing
release attempts exist for the same version, stop and ask the user which attempt is authoritative.
