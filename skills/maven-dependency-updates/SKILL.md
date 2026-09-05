---
name: maven-dependency-updates
description: Check or update Maven dependency and plugin versions. Applies to version upgrades, not arbitrary pom.xml edits.
---
# Maven dependency updates

Distinguish a report-only request from an update request. Checking for newer versions
produces a report without edits. An update request authorizes the specified upgrades and
necessary compatible fixes within that scope; do not ask the user to approve them again.
Ask only when a material version, compatibility, or scope choice cannot be resolved from
the request and repository constraints.

## Discover and apply

Use the repository's Maven wrapper or configured Maven environment. For a general update
survey, run from the root POM:

```text
mvn versions:display-dependency-updates
mvn versions:display-plugin-updates
```

Narrow reporting for a specific requested upgrade. Report artifact coordinates and old
and proposed versions. Default to stable releases; distinguish alpha, beta, RC, milestone,
and snapshot versions. Preserve explicit version and compatibility constraints.

Update shared properties or dependencyManagement/pluginManagement declarations at their
source. Do not bump unrelated dependencies. Inspect release or migration guidance when
compatibility changes could affect the upgrade.

## Verify and finish

Run affected-module builds and tests while iterating, then the repository's required
verification gate for the completed upgrade. Use `mvn clean verify` when that is the
appropriate project gate. Run `dependency:resolve` separately only when diagnosing
resolution or when specifically required; a successful build already resolves its inputs.

Investigate failures and fix those caused by the requested upgrade when the fixes preserve
the intended behavior and fit the authorized scope. Rerun affected checks after fixes.
Do not weaken tests or change public behavior merely to make an upgrade pass. For a
material migration beyond scope, complete independent upgrades and present the concrete
remaining choice. Honor a request limited to POM edits.

Report applied versions, verification results, and any deferred upgrades or unresolved
failures. Distinguish pre-existing failures from regressions when evidence permits.
