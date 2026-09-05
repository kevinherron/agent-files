#!/usr/bin/env bash
# shellcheck shell=bash
# Generate YAML frontmatter for a new or updated research document.

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  research-metadata.sh --topic TEXT [--tags CSV] [--status STATUS]
                       [--repo PATH] [--researcher NAME]
  research-metadata.sh --update [--note TEXT] [--repo PATH]
                       [--researcher NAME]

Statuses: draft, in-progress, complete

Omit --repo for non-repository research. When supplied, PATH must be inside the
repository being researched, not merely the directory receiving the document.
EOF
}

die() {
    printf 'error: %s\n' "$*" >&2
    exit 2
}

require_value() {
    local option="$1"
    local remaining="$2"
    local next_value="${3:-}"
    [[ "$remaining" -ge 2 && -n "$next_value" && "$next_value" != --* ]] ||
        die "$option requires a value"
}

escape_yaml() {
    local value="$1"
    value=${value//\\/\\\\}
    value=${value//\"/\\\"}
    value=${value//$'\n'/\\n}
    value=${value//$'\r'/\\r}
    printf '%s' "$value"
}

yaml_string() {
    printf '"%s"' "$(escape_yaml "$1")"
}

trim() {
    local value="$1"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

TOPIC=""
TAGS="research"
STATUS="complete"
REPO_PATH=""
RESEARCHER=""
UPDATE_MODE=false
UPDATE_NOTE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --topic)
            require_value "$1" "$#" "${2:-}"
            TOPIC="$2"
            shift 2
            ;;
        --tags)
            require_value "$1" "$#" "${2:-}"
            TAGS="$2"
            shift 2
            ;;
        --status)
            require_value "$1" "$#" "${2:-}"
            STATUS="$2"
            shift 2
            ;;
        --repo)
            require_value "$1" "$#" "${2:-}"
            REPO_PATH="$2"
            shift 2
            ;;
        --researcher)
            require_value "$1" "$#" "${2:-}"
            RESEARCHER="$2"
            shift 2
            ;;
        --update)
            UPDATE_MODE=true
            shift
            ;;
        --note)
            require_value "$1" "$#" "${2:-}"
            UPDATE_NOTE="$2"
            shift 2
            ;;
        *)
            die "unknown option: $1"
            ;;
    esac
done

case "$STATUS" in
    draft|in-progress|complete) ;;
    *) die "invalid status '$STATUS' (expected draft, in-progress, or complete)" ;;
esac

if [[ "$UPDATE_MODE" == true ]]; then
    [[ -z "$TOPIC" ]] || die "--topic is not valid with --update"
    [[ "$TAGS" == "research" ]] || die "--tags is not valid with --update"
    [[ "$STATUS" == "complete" ]] || die "--status is not valid with --update"
else
    [[ -n "$(trim "$TOPIC")" ]] || die "--topic is required for a new document"
fi

if [[ -n "$REPO_PATH" ]]; then
    [[ -d "$REPO_PATH" ]] || die "repository path does not exist: $REPO_PATH"
    git -C "$REPO_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
        die "--repo is not inside a Git repository: $REPO_PATH"
fi

if [[ -z "$RESEARCHER" ]]; then
    if [[ -n "$REPO_PATH" ]]; then
        RESEARCHER=$(git -C "$REPO_PATH" config user.name 2>/dev/null || true)
    fi
    if [[ -z "$RESEARCHER" ]]; then
        RESEARCHER=$(git config --global user.name 2>/dev/null || true)
    fi
    if [[ -z "$RESEARCHER" ]]; then
        RESEARCHER="${USER:-Unknown}"
    fi
fi

DATE_ISO=$(date +"%Y-%m-%dT%H:%M:%S%z" | sed 's/\([+-][0-9][0-9]\)\([0-9][0-9]\)$/\1:\2/')

emit_repository_fields() {
    local commit branch repository dirty
    commit=$(git -C "$REPO_PATH" rev-parse HEAD)
    branch=$(git -C "$REPO_PATH" branch --show-current)
    [[ -n "$branch" ]] || branch="detached"
    repository=$(basename "$(git -C "$REPO_PATH" rev-parse --show-toplevel)")
    dirty=false
    [[ -z "$(git -C "$REPO_PATH" status --porcelain)" ]] || dirty=true

    printf 'repository: %s\n' "$(yaml_string "$repository")"
    printf 'git_commit: %s\n' "$(yaml_string "$commit")"
    printf 'branch: %s\n' "$(yaml_string "$branch")"
    printf 'dirty: %s\n' "$dirty"
}

if [[ "$UPDATE_MODE" == true ]]; then
    printf 'last_updated: %s\n' "$(yaml_string "$DATE_ISO")"
    printf 'last_updated_by: %s\n' "$(yaml_string "$RESEARCHER")"
    if [[ -n "$UPDATE_NOTE" ]]; then
        printf 'last_updated_note: %s\n' "$(yaml_string "$UPDATE_NOTE")"
    fi
    if [[ -n "$REPO_PATH" ]]; then
        emit_repository_fields
    fi
    exit 0
fi

IFS=',' read -r -a tag_values <<< "$TAGS"
tags_yaml="["
tag_count=0
for raw_tag in "${tag_values[@]}"; do
    tag=$(trim "$raw_tag")
    [[ -n "$tag" ]] || die "tags must not contain empty values"
    if [[ "$tag_count" -gt 0 ]]; then
        tags_yaml+=", "
    fi
    tags_yaml+="$(yaml_string "$tag")"
    tag_count=$((tag_count + 1))
done
tags_yaml+="]"
[[ "$tag_count" -gt 0 ]] || die "at least one tag is required"

printf '%s\n' '---'
printf 'date: %s\n' "$(yaml_string "$DATE_ISO")"
printf 'researcher: %s\n' "$(yaml_string "$RESEARCHER")"
if [[ -n "$REPO_PATH" ]]; then
    emit_repository_fields
fi
printf 'topic: %s\n' "$(yaml_string "$TOPIC")"
printf 'tags: %s\n' "$tags_yaml"
printf 'status: %s\n' "$(yaml_string "$STATUS")"
printf 'last_updated: %s\n' "$(yaml_string "$DATE_ISO")"
printf 'last_updated_by: %s\n' "$(yaml_string "$RESEARCHER")"
printf '%s\n' '---'
