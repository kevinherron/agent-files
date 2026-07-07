#!/usr/bin/env bash
# shellcheck shell=bash
# Generate YAML frontmatter metadata for research documents
#
# Usage:
#   New document:
#     research-metadata.sh [--topic "topic"] [--tags "tag1,tag2,tag3"] [--status "status"] [--repo /path/to/repo]
#
#   Update existing document:
#     research-metadata.sh --update [--note "description of changes"]
#
# Git metadata (commit, branch, repository, dirty flag) is read from --repo if given,
# otherwise from the current directory. Point it at the repository the research is
# ABOUT, not the repository the document lives in.
#
# Examples:
#   ./research-metadata.sh --topic "Authentication flow analysis" --tags "research,auth,gateway"
#   ./research-metadata.sh --repo ~/src/milo --topic "Session lifecycle survey"
#   ./research-metadata.sh --update --note "Added follow-up on token refresh"

set -euo pipefail

usage() {
    awk 'NR > 2 { if ($0 !~ /^#/) exit; sub(/^# ?/, ""); print }' "$0"
    exit 0
}

# Escape backslashes and double quotes for YAML double-quoted string safety
escape_yaml() {
    local s="${1//\\/\\\\}"
    printf '%s' "${s//\"/\\\"}"
}

# Trim leading and trailing whitespace
trim() {
    local s="$1"
    s="${s#"${s%%[![:space:]]*}"}"
    s="${s%"${s##*[![:space:]]}"}"
    printf '%s' "$s"
}

# Defaults
TOPIC=""
TAGS="research,codebase"
STATUS="complete"
REPO_PATH="."
UPDATE_MODE=false
UPDATE_NOTE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        --topic)
            TOPIC="$2"
            shift 2
            ;;
        --tags)
            TAGS="$2"
            shift 2
            ;;
        --status)
            STATUS="$2"
            shift 2
            ;;
        --repo)
            REPO_PATH="$2"
            shift 2
            ;;
        --update)
            UPDATE_MODE=true
            shift
            ;;
        --note)
            UPDATE_NOTE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Gather metadata
# Format timezone as +00:00 instead of +0000 for ISO 8601 compliance
DATE_ISO=$(date +"%Y-%m-%dT%H:%M:%S%z" | sed 's/\([+-][0-9][0-9]\)\([0-9][0-9]\)$/\1:\2/')
RESEARCHER=$(git -C "$REPO_PATH" config user.name 2>/dev/null || echo "Unknown")

# Update mode: output only the fields needed to update existing frontmatter
if [[ "$UPDATE_MODE" == true ]]; then
    echo "last_updated: ${DATE_ISO}"
    echo "last_updated_by: ${RESEARCHER}"
    if [[ -n "$UPDATE_NOTE" ]]; then
        echo "last_updated_note: \"$(escape_yaml "$UPDATE_NOTE")\""
    fi
    exit 0
fi

# Full frontmatter mode
GIT_COMMIT=$(git -C "$REPO_PATH" rev-parse HEAD 2>/dev/null || echo "unknown")
BRANCH=$(git -C "$REPO_PATH" branch --show-current 2>/dev/null || echo "unknown")
REPO=$(basename "$(git -C "$REPO_PATH" rev-parse --show-toplevel 2>/dev/null || echo "unknown")")
DIRTY=false
if [[ -n "$(git -C "$REPO_PATH" status --porcelain 2>/dev/null)" ]]; then
    DIRTY=true
fi

# Convert comma-separated tags to YAML array format
IFS=',' read -ra TAG_ARRAY <<< "$TAGS"
TAGS_YAML="["
for i in "${!TAG_ARRAY[@]}"; do
    if [[ $i -gt 0 ]]; then
        TAGS_YAML+=", "
    fi
    tag=$(trim "${TAG_ARRAY[$i]}")
    TAGS_YAML+="\"$(escape_yaml "$tag")\""
done
TAGS_YAML+="]"

# Escape topic for YAML output
TOPIC_ESCAPED=$(escape_yaml "$TOPIC")

# Output YAML frontmatter
cat << EOF
---
date: ${DATE_ISO}
researcher: ${RESEARCHER}
git_commit: ${GIT_COMMIT}
branch: ${BRANCH}
repository: ${REPO}
EOF
if [[ "$DIRTY" == true ]]; then
    echo "dirty: true"
fi
cat << EOF
topic: "${TOPIC_ESCAPED}"
tags: ${TAGS_YAML}
status: ${STATUS}
last_updated: ${DATE_ISO}
last_updated_by: ${RESEARCHER}
---
EOF
