#!/usr/bin/env python3
"""Persist resumable GitHub/Maven release state in a repository's Git metadata."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any


STATE_FILE_NAME = "codex-gh-maven-release.json"
SETTABLE_KEYS = {
    "phase",
    "base_sha",
    "version_commit_sha",
    "release_sha",
    "release_branch_remote_sha",
    "release_id",
    "release_url",
    "tag_sha",
    "published_at",
    "workflow_file",
    "workflow_event",
    "workflow_run_id",
    "workflow_url",
    "deployment_id",
    "snapshot_commit_sha",
    "pr_url",
    "failure_classification",
}


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def state_path() -> Path:
    git_common_dir = Path(run_git("rev-parse", "--git-common-dir"))
    if not git_common_dir.is_absolute():
        git_common_dir = (Path.cwd() / git_common_dir).resolve()
    return git_common_dir / STATE_FILE_NAME


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"no release state found at {path}")
    with path.open(encoding="utf-8") as state_file:
        value = json.load(state_file)
    if not isinstance(value, dict):
        raise SystemExit(f"invalid release state at {path}: expected a JSON object")
    return value


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as state_file:
        json.dump(state, state_file, indent=2, sort_keys=True)
        state_file.write("\n")
    temporary.replace(path)


def initialize(args: argparse.Namespace) -> None:
    path = state_path()
    if path.exists():
        raise SystemExit(
            f"release state already exists at {path}; show or archive it before initializing"
        )
    repository_root = run_git("rev-parse", "--show-toplevel")
    state = {
        "schema_version": 1,
        "repository_root": repository_root,
        "repository": args.repository,
        "base_branch": args.base_branch,
        "release_branch": args.release_branch,
        "version": args.version,
        "next_version": args.next_version,
        "tag": args.tag,
        "phase": "initialized",
        "created_at": now(),
        "updated_at": now(),
    }
    write_state(path, state)
    print(path)


def show(_: argparse.Namespace) -> None:
    path = state_path()
    print(json.dumps(read_state(path), indent=2, sort_keys=True))


def show_path(_: argparse.Namespace) -> None:
    print(state_path())


def set_value(args: argparse.Namespace) -> None:
    path = state_path()
    state = read_state(path)
    state[args.key] = args.value
    state["updated_at"] = now()
    write_state(path, state)
    print(f"{args.key}={args.value}")


def archive(_: argparse.Namespace) -> None:
    path = state_path()
    state = read_state(path)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archived_path = path.with_name(f"{path.stem}-{timestamp}.json")
    if archived_path.exists():
        raise SystemExit(f"archive already exists at {archived_path}")
    state["archived_at"] = now()
    write_state(path, state)
    path.replace(archived_path)
    print(archived_path)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    init_parser = commands.add_parser("init", help="initialize state for a new release")
    init_parser.add_argument("--repository", required=True, help="OWNER/REPO")
    init_parser.add_argument("--base-branch", required=True)
    init_parser.add_argument("--release-branch", required=True)
    init_parser.add_argument("--version", required=True)
    init_parser.add_argument("--next-version", required=True)
    init_parser.add_argument("--tag", required=True)
    init_parser.set_defaults(function=initialize)

    show_parser = commands.add_parser("show", help="print current state as JSON")
    show_parser.set_defaults(function=show)

    path_parser = commands.add_parser("path", help="print the current state path")
    path_parser.set_defaults(function=show_path)

    set_parser = commands.add_parser("set", help="update a mutable release-state field")
    set_parser.add_argument("key", choices=sorted(SETTABLE_KEYS))
    set_parser.add_argument("value")
    set_parser.set_defaults(function=set_value)

    archive_parser = commands.add_parser("archive", help="archive completed release state")
    archive_parser.set_defaults(function=archive)

    return root


def main() -> None:
    args = parser().parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
