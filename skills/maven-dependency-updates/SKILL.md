---
name: maven-dependency-updates
description: "Check a Maven project for newer dependency and plugin versions using the versions plugin, then optionally apply them. Use this skill whenever the user wants to update Maven dependencies or plugins, check for outdated versions, run versions:display-dependency-updates or versions:display-plugin-updates, 'bump dependencies', 'check for dependency updates', 'update the pom', or otherwise look for available version upgrades in a Maven (pom.xml) project."
---
Use the Maven versions plugin to look for dependency and plugin version updates,
present them to the user, and apply the ones they approve.

## Process

### 1. Check for updates

Run both report goals from the directory containing the root `pom.xml`:

```
mvn versions:display-dependency-updates
mvn versions:display-plugin-updates
```

- `versions:display-dependency-updates` reports dependencies that have newer
  versions available.
- `versions:display-plugin-updates` reports build plugins that have newer
  versions available.

These goals only **report**; they do not modify any files.

In a multi-module (reactor) build, run the goals from the root and they will cover
the whole project.

### 2. Summarize and present

Parse the output and present a clear summary to the user, grouped into
**dependencies** and **plugins**. For each entry show the artifact (groupId:artifactId),
the current version, and the proposed new version.

Flag non-stable versions explicitly. The plugin will often suggest alpha, beta, RC,
milestone, or snapshot versions — call these out separately and default to
recommending the latest **stable release** unless the user asks otherwise.

Then ask the user whether they want to apply the updates, and which ones (all, or a
subset). **Do not modify anything until the user responds.**

If the user does **not** want to apply updates, there is nothing further to do. Stop here.

### 3. Apply the approved updates

Edit the `pom.xml` file(s) directly to set the approved versions.

- Prefer editing the **version property** (e.g. `<some.lib.version>`) when the version
  is defined in `<properties>` and reused — change it in one place rather than at each
  declaration site.
- Otherwise edit the `<version>` element on the specific dependency or plugin.
- In multi-module projects, versions are usually declared once in the parent's
  `<dependencyManagement>` / `<pluginManagement>` or in `<properties>`; update there.
- Apply only the versions the user approved. Do not silently bump anything else.

### 4. Verify dependencies resolve

```
mvn dependency:resolve
```

If there are resolution errors (e.g. a version doesn't exist, or a coordinate
changed), fix them — correct the version, adjust the coordinate, or revert that
specific update — then re-run until resolution succeeds.

### 5. Verify the build and tests

```
mvn clean verify
```

This ensures the project still compiles and the tests pass with the new versions.

**If there are errors at this stage, investigate and make suggestions to the user,
but do not modify any code.** The goal of this step is to confirm whether the version
updates are safe — not to refactor the project to accommodate them. Report what broke
and what you'd recommend (e.g. a migration step, a different version, or reverting a
particular update), and let the user decide.

## Guidelines

- Only the version-application step (3) changes files. Steps 1, 4, and 5 are read/verify.
- Keep the user in control: present first, apply only what's approved.
- Default to stable releases; surface pre-release/snapshot suggestions but don't apply
  them unless asked.
- If a build fails after updating, never edit source code to make it pass — investigate
  and advise instead.
