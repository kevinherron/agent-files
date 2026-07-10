#!/usr/bin/env python3
"""Validate deterministic structural invariants in a finished implementation plan."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


H2_RE = re.compile(r"^## (.+)$", re.MULTILINE)
WORK_PACKAGE_RE = re.compile(r"^## Work Package (\d+):\s+(.+)$", re.MULTILINE)
DECLARATION_RE = re.compile(
    r"^\*\*(File|New file|Destination|Artifact):\*\*\s*(.+)$", re.MULTILINE
)
BACKTICK_RE = re.compile(r"`([^`]+)`")
PLACEHOLDER_HINTS = (
    "feature name",
    "authoritative source",
    "feature-slug",
    "ready | conditional | draft",
    "path or none",
    "branch, commit",
    "wpx",
    "title",
    "capability or",
    "material decision",
    "person, design",
    "trigger",
    "purpose",
    "package-or-module",
    "optional formatter",
    "targeted tests",
    "full required verification",
    "summary or links",
    "summary and rationale",
    "commands and results",
    "configuration or re-grounding",
    "concise list",
)


@dataclass(frozen=True)
class Section:
    heading: str
    body: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a completed implementation-plan Markdown file."
    )
    parser.add_argument("plan", type=Path, help="Path to the Markdown plan")
    return parser.parse_args()


def h2_sections(text: str) -> dict[str, Section]:
    matches = list(H2_RE.finditer(text))
    sections: dict[str, Section] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        heading = match.group(1).strip()
        sections[heading] = Section(heading, text[match.end() : end])
    return sections


def slugify(heading: str) -> str:
    value = heading.replace("`", "").strip().lower()
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    return value.strip("-")


def heading_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+)$", line)
        if not match:
            continue
        base = slugify(match.group(1))
        count = counts.get(base, 0)
        anchors.add(base if count == 0 else f"{base}-{count}")
        counts[base] = count + 1
    return anchors


def metadata_value(text: str, label: str) -> str | None:
    match = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip().strip("`") if match else None


def placeholder_errors(text: str) -> list[str]:
    errors: list[str] = []
    if "<!--" in text or "-->" in text:
        errors.append("HTML template comments remain")
    if re.search(r"\b(?:TBD|TODO)\b", text, re.IGNORECASE):
        errors.append("unresolved TBD/TODO marker remains")
    if "…" in text:
        errors.append("template ellipsis remains")

    for match in re.finditer(r"\[([^\]\n]+)\]", text):
        value = match.group(1).strip().lower()
        if any(hint in value for hint in PLACEHOLDER_HINTS):
            errors.append(f"template placeholder remains: [{match.group(1)}]")
    return errors


def validate_metadata(text: str, sections: dict[str, Section]) -> tuple[str | None, list[str]]:
    errors: list[str] = []
    plan_id = metadata_value(text, "Plan ID")
    status = metadata_value(text, "Status")
    parent = metadata_value(text, "Parent manifest")
    grounded = metadata_value(text, "Grounded against")
    reground = metadata_value(text, "Re-ground before")

    for label, value in (
        ("Plan ID", plan_id),
        ("Status", status),
        ("Parent manifest", parent),
        ("Grounded against", grounded),
        ("Re-ground before", reground),
    ):
        if not value:
            errors.append(f"missing {label} metadata")

    if status and status not in {"Ready", "Conditional", "Draft"}:
        errors.append("Status must be Ready, Conditional, or Draft")

    open_decisions = sections.get("Open Decisions")
    if status == "Ready" and open_decisions:
        errors.append("Ready plan must omit Open Decisions")
    if status in {"Conditional", "Draft"} and not open_decisions:
        errors.append(f"{status} plan requires an Open Decisions section")
    if status in {"Conditional", "Draft"} and open_decisions:
        decision_rows = [
            line
            for line in open_decisions.body.splitlines()
            if line.startswith("|")
            and "Decision" not in line
            and not re.fullmatch(r"\|[\s|:-]+\|", line)
        ]
        if not decision_rows:
            errors.append(f"{status} plan requires at least one Open Decisions data row")
    if status == "Conditional" and reground and reground.lower() == "none":
        errors.append("Conditional plan requires a named re-grounding trigger")

    return status, errors


def validate_work_packages(text: str, sections: dict[str, Section]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    identifiers: list[str] = []
    packages = list(WORK_PACKAGE_RE.finditer(text))
    if not packages:
        return identifiers, ["no Work Package headings found"]

    h2_matches = list(H2_RE.finditer(text))
    for package in packages:
        next_h2 = next((match.start() for match in h2_matches if match.start() > package.start()), len(text))
        body = text[package.end() : next_h2]
        number = package.group(1)
        expected_id = f"WP{number}"

        package_id = metadata_value(body, "ID")
        if not package_id:
            errors.append(f"{expected_id} is missing ID")
        else:
            identifiers.append(package_id)
            if package_id != expected_id:
                errors.append(f"Work Package {number} ID must be {expected_id}, found {package_id}")

        for label in ("Depends on", "Done when", "Checkpoint"):
            if not metadata_value(body, label):
                errors.append(f"{expected_id} is missing {label}")

        for heading in ("Tests", "Verification", "Implementation Notes"):
            if not re.search(rf"^### {re.escape(heading)}\s*$", body, re.MULTILINE):
                errors.append(f"{expected_id} is missing {heading}")

        h3_matches = list(re.finditer(r"^### (.+)$", body, re.MULTILINE))
        subtask_matches = [
            match for match in h3_matches if re.match(rf"{number}\.\d+\s+", match.group(1))
        ]
        if not subtask_matches:
            errors.append(f"{expected_id} has no numbered subtasks")
        for subtask in subtask_matches:
            end = next(
                (match.start() for match in h3_matches if match.start() > subtask.start()),
                len(body),
            )
            subtask_body = body[subtask.end() : end]
            if not DECLARATION_RE.search(subtask_body):
                errors.append(f"{expected_id} subtask '{subtask.group(0)}' has no file/artifact declaration")

    if len(identifiers) != len(set(identifiers)):
        errors.append("work-package IDs are not unique")

    progress = sections.get("Progress")
    if progress:
        checkbox_lines = [
            line for line in progress.body.splitlines() if re.match(r"^\s*- \[[ xX]\]", line)
        ]
        if any(line.startswith((" ", "\t")) for line in checkbox_lines):
            errors.append("Progress must not duplicate indented subtask checkboxes")
        if len(checkbox_lines) != len(packages):
            errors.append("Progress must contain exactly one checkbox per work package")
        for identifier in identifiers:
            if not any(identifier in line for line in checkbox_lines):
                errors.append(f"Progress is missing {identifier}")

    return identifiers, errors


def validate_files(text: str, sections: dict[str, Section], status: str | None) -> list[str]:
    errors: list[str] = []
    declarations: list[tuple[str, str]] = []
    for match in DECLARATION_RE.finditer(text):
        kind = match.group(1)
        paths = BACKTICK_RE.findall(match.group(2))
        if not paths:
            errors.append(f"{kind} declaration must contain a backticked path or destination")
            continue
        declarations.extend((kind, path) for path in paths)

    if status == "Ready" and any(kind == "Destination" for kind, _ in declarations):
        errors.append("Ready plan must not contain Destination declarations")

    inventory = sections.get("File Inventory")
    work_package_count = len(WORK_PACKAGE_RE.findall(text))
    if work_package_count > 1 and not inventory:
        errors.append("multi-work-package plan requires a File Inventory")
    if inventory:
        for _, path in declarations:
            if path not in inventory.body:
                errors.append(f"File Inventory is missing declared path: {path}")
    return errors


def validate_links(text: str) -> list[str]:
    errors: list[str] = []
    anchors = heading_anchors(text)
    for anchor in re.findall(r"\]\(#([^)]+)\)", text):
        if anchor not in anchors:
            errors.append(f"internal link target does not exist: #{anchor}")
    return errors


def validate(plan: Path) -> list[str]:
    try:
        text = plan.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read plan: {exc}"]

    sections = h2_sections(text)
    errors = placeholder_errors(text)
    status, metadata_errors = validate_metadata(text, sections)
    errors.extend(metadata_errors)
    _, work_package_errors = validate_work_packages(text, sections)
    errors.extend(work_package_errors)
    errors.extend(validate_files(text, sections, status))
    errors.extend(validate_links(text))
    return errors


def main() -> int:
    args = parse_args()
    errors = validate(args.plan)
    if errors:
        print(f"Implementation plan validation failed: {args.plan}", file=sys.stderr)
        for error in dict.fromkeys(errors):
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Implementation plan is valid: {args.plan}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
