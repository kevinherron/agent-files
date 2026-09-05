#!/usr/bin/env python3
"""Validate deterministic structural invariants of a Markdown research document."""

from __future__ import annotations

import argparse
import ast
from datetime import datetime
from pathlib import Path
import re
import sys
from typing import Optional


REQUIRED_FIELDS = (
    "date",
    "researcher",
    "topic",
    "tags",
    "status",
    "last_updated",
    "last_updated_by",
)
ALLOWED_STATUSES = {"draft", "in-progress", "complete"}
STRING_FIELDS = {
    "date",
    "researcher",
    "repository",
    "git_commit",
    "branch",
    "topic",
    "status",
    "last_updated",
    "last_updated_by",
    "last_updated_note",
}


def parse_scalar(value: str, line_number: int) -> object:
    value = value.strip()
    if not value:
        return ""
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith(('"', "'", "[")):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise ValueError(f"line {line_number}: malformed scalar or array") from exc
    if re.search(r":\s", value) or value.startswith(("{", "|", ">", "&", "*", "!")):
        raise ValueError(f"line {line_number}: unsupported or ambiguous YAML value")
    return value


def parse_frontmatter(
    lines: list[str], end_index: int
) -> tuple[dict[str, object], list[str]]:
    data: dict[str, object] = {}
    errors: list[str] = []
    for index, line in enumerate(lines[1:end_index], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)", line)
        if not match:
            errors.append(f"line {index}: unsupported or malformed frontmatter")
            continue
        key, raw_value = match.groups()
        if key in data:
            errors.append(f"line {index}: duplicate frontmatter key '{key}'")
            continue
        try:
            data[key] = parse_scalar(raw_value, index)
        except ValueError as exc:
            errors.append(str(exc))
    return data, errors


def validate_iso8601(field: str, value: object, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"frontmatter '{field}' must be a quoted string")
        return
    try:
        datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"frontmatter '{field}' is not an ISO 8601 timestamp")


def markdown_headings(body: list[str]) -> list[tuple[int, str, int]]:
    headings: list[tuple[int, str, int]] = []
    fence: Optional[str] = None
    for line_number, line in enumerate(body, start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            fence = None if fence == marker else marker if fence is None else fence
            continue
        if fence is not None:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append((len(match.group(1)), match.group(2), line_number))
    return headings


def validate(path: Path, strict: bool) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read {path}: {exc}")
        return 1
    except UnicodeDecodeError:
        print(f"ERROR: {path} is not valid UTF-8")
        return 1

    if not text.startswith("---\n"):
        errors.append("document must start with YAML frontmatter delimited by '---'")
        lines = text.splitlines()
        frontmatter: dict[str, object] = {}
        body = lines
    else:
        lines = text.splitlines()
        try:
            end_index = lines.index("---", 1)
        except ValueError:
            errors.append("frontmatter is missing its closing '---' delimiter")
            frontmatter = {}
            body = []
        else:
            frontmatter, parse_errors = parse_frontmatter(lines, end_index)
            errors.extend(parse_errors)
            body = lines[end_index + 1 :]

    for field in REQUIRED_FIELDS:
        if field not in frontmatter:
            errors.append(f"missing required frontmatter field '{field}'")

    for field in STRING_FIELDS & frontmatter.keys():
        value = frontmatter[field]
        if not isinstance(value, str):
            errors.append(f"frontmatter '{field}' must be a quoted string")
        elif field in REQUIRED_FIELDS and not value.strip():
            errors.append(f"frontmatter '{field}' must not be empty")

    if "date" in frontmatter:
        validate_iso8601("date", frontmatter["date"], errors)
    if "last_updated" in frontmatter:
        validate_iso8601("last_updated", frontmatter["last_updated"], errors)

    status = frontmatter.get("status")
    if isinstance(status, str) and status not in ALLOWED_STATUSES:
        errors.append("frontmatter 'status' must be draft, in-progress, or complete")

    tags = frontmatter.get("tags")
    if (
        not isinstance(tags, list)
        or not tags
        or not all(isinstance(tag, str) and tag.strip() for tag in tags)
    ):
        errors.append("frontmatter 'tags' must be a non-empty quoted string array")
    elif "research" not in tags:
        warnings.append("frontmatter tags do not include 'research'")

    dirty = frontmatter.get("dirty")
    if dirty is not None and not isinstance(dirty, bool):
        errors.append("frontmatter 'dirty' must be true or false")

    repository_fields = {"repository", "git_commit", "branch", "dirty"}
    present_repository_fields = repository_fields & frontmatter.keys()
    if present_repository_fields and present_repository_fields != repository_fields:
        missing = ", ".join(sorted(repository_fields - present_repository_fields))
        errors.append(f"repository metadata is incomplete; missing: {missing}")

    headings = markdown_headings(body)
    h1s = [heading for heading in headings if heading[0] == 1]
    if len(h1s) != 1:
        errors.append(f"document must contain exactly one H1 title; found {len(h1s)}")
    elif not h1s[0][1].strip():
        errors.append("H1 title must not be empty")

    first_body_content = next((line.strip() for line in body if line.strip()), "")
    if first_body_content and not first_body_content.startswith("# "):
        warnings.append("the first non-empty body line should be the H1 title")

    if h1s:
        h1_index = next(
            (index for index, line in enumerate(body) if line.startswith("# ")),
            None,
        )
        if h1_index is not None:
            summary_found = False
            for line in body[h1_index + 1 :]:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("## "):
                    break
                if not stripped.startswith(("#", "<!--")):
                    summary_found = True
                    break
            if not summary_found:
                warnings.append("no opening summary found between the H1 and first H2")

    lower_body = "\n".join(body).lower()
    if "open question" not in lower_body and "unresolved" not in lower_body:
        warnings.append(
            "document does not identify open questions or explicitly state that none remain"
        )

    if text and not text.endswith("\n"):
        warnings.append("document should end with a newline")

    if strict:
        errors.extend(f"strict: {warning}" for warning in warnings)
        warnings = []

    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARNING: {warning}")

    if errors:
        print(f"FAIL: {path} ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1
    print(f"OK: {path} ({len(warnings)} warning(s))")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate structural invariants of a Markdown research document."
    )
    parser.add_argument("document", type=Path)
    parser.add_argument(
        "--strict", action="store_true", help="treat judgment warnings as errors"
    )
    args = parser.parse_args()
    return validate(args.document, args.strict)


if __name__ == "__main__":
    sys.exit(main())
