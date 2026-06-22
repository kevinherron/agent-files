#!/usr/bin/env bash
#
# Resolve an idea-inspections scope spec to a newline-delimited list of
# project-relative Java/Kotlin file paths. Run from anywhere inside the repo;
# the script re-roots itself at the git toplevel and emits repo-relative paths.
#
# Usage: resolve-scope.sh [SCOPE]
#
#   (no arg) | changed | git   Java/Kotlin files changed vs HEAD
#                              (tracked modifications + staged + untracked)
#   all                        Every tracked Java/Kotlin file
#   module:<name>              Files under <name>/ (a Maven/Gradle module dir)
#   package:<a.b.c>            Files under any .../a/b/c/ (recursive)
#   dir:<path>                 Files under <path>/ (recursive)
#   file:<path>                The single file, if Java/Kotlin
#
# Only existing .java/.kt files are emitted, de-duplicated and sorted.
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
cd "$root"

scope="${1:-changed}"

is_code() { case "$1" in *.java | *.kt) return 0 ;; *) return 1 ;; esac; }

# Read paths on stdin; keep existing Java/Kotlin files, de-duped + sorted.
emit_existing() {
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    is_code "$f" || continue
    [ -f "$f" ] || continue
    printf '%s\n' "$f"
  done | LC_ALL=C sort -u
}

all_code() { git ls-files -- '*.java' '*.kt'; }

case "$scope" in
  changed | git | "")
    {
      git diff --name-only HEAD --
      git diff --name-only --cached --
      git ls-files --others --exclude-standard
    } | emit_existing
    ;;
  all)
    all_code | emit_existing
    ;;
  module:*)
    name="${scope#module:}"
    all_code | grep -E "^${name}/" | emit_existing
    ;;
  package:*)
    pkg="${scope#package:}"
    path="${pkg//.//}"
    all_code | grep -E "(^|/)${path}/" | emit_existing
    ;;
  dir:*)
    d="${scope#dir:}"
    d="${d%/}"
    all_code | grep -E "^${d}/" | emit_existing
    ;;
  file:*)
    printf '%s\n' "${scope#file:}" | emit_existing
    ;;
  *)
    echo "resolve-scope.sh: unknown scope '$scope'" >&2
    exit 2
    ;;
esac
