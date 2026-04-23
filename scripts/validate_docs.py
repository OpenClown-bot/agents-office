#!/usr/bin/env python3
"""Validate all markdown artifacts in docs/.

Checks:
- YAML frontmatter is present and parseable
- Required fields are present per artifact type
- `status` is from the allowed set for that type
- Version-pinned references (`PRD-XXX@X.Y.Z`, `ARCH-XXX@X.Y.Z`, `ADR-XXX@X.Y.Z`)
  actually resolve to existing artifacts
- TEMPLATE.md files are ignored
- `supersedes` / `superseded_by` refer to real artifacts

Exit 0 on success, 1 on any failure. Used by CI.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
REF_RE = re.compile(r"\b(PRD|ARCH|ADR|TKT)-(\d{3,})@(\d+\.\d+\.\d+)")

# (required_fields, allowed_statuses)
TYPE_RULES: dict[str, tuple[set[str], set[str]]] = {
    "prd": (
        {"id", "title", "version", "status", "owner", "created"},
        {"draft", "in_review", "approved", "superseded"},
    ),
    "architecture": (
        {"id", "title", "version", "status", "prd_ref", "owner", "created"},
        {"draft", "in_review", "approved", "superseded"},
    ),
    "adr": (
        {"id", "title", "status", "arch_ref", "created"},
        {"proposed", "accepted", "rejected", "superseded"},
    ),
    "tickets": (
        {"id", "title", "status", "arch_ref", "assigned_executor", "created"},
        {"draft", "ready", "in_progress", "in_review", "done", "blocked"},
    ),
    "reviews": (
        {"id", "type", "status", "reviewer_model", "created"},
        {"in_review", "approved", "changes_requested"},
    ),
    "questions": (
        {"id", "status", "ticket_ref", "asker_model", "created"},
        {"open", "answered", "superseded"},
    ),
}

ID_PREFIX_FOR_TYPE = {
    "prd": "PRD",
    "architecture": "ARCH",
    "adr": "ADR",
    "tickets": "TKT",
    "reviews": "RV",
    "questions": "Q",
}


@dataclass
class Artifact:
    path: Path
    type_: str
    frontmatter: dict
    body: str


def load_artifact(path: Path) -> Artifact | None:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parse error in {path}: {e}") from e
    body = text[m.end():]
    # determine type by directory
    rel = path.relative_to(DOCS_ROOT)
    parts = rel.parts
    type_ = parts[0]
    # adr is under architecture/adr
    if type_ == "architecture" and len(parts) > 1 and parts[1] == "adr":
        type_ = "adr"
    return Artifact(path=path, type_=type_, frontmatter=fm, body=body)


def collect_known_ids() -> set[str]:
    known: set[str] = set()
    for md in DOCS_ROOT.rglob("*.md"):
        if md.name.startswith("TEMPLATE"):
            continue
        try:
            art = load_artifact(md)
        except ValueError:
            continue
        if art is None:
            continue
        art_id = art.frontmatter.get("id")
        if isinstance(art_id, str):
            known.add(art_id)
    return known


def validate_artifact(art: Artifact, known_ids: set[str]) -> list[str]:
    errors: list[str] = []
    rules = TYPE_RULES.get(art.type_)
    if rules is None:
        return [f"unknown artifact type directory: {art.type_}"]
    required, statuses = rules

    # Required frontmatter fields
    for field in required:
        if field not in art.frontmatter or art.frontmatter[field] in (None, ""):
            errors.append(f"missing required frontmatter field: {field}")

    # Status value
    status = art.frontmatter.get("status")
    if status and status not in statuses:
        errors.append(f"invalid status '{status}'; allowed: {sorted(statuses)}")

    # ID prefix matches directory
    art_id = art.frontmatter.get("id", "")
    expected_prefix = ID_PREFIX_FOR_TYPE.get(art.type_)
    if expected_prefix and isinstance(art_id, str) and art_id != f"{expected_prefix}-XXX":
        if not art_id.startswith(expected_prefix + "-"):
            errors.append(
                f"id '{art_id}' does not match directory prefix '{expected_prefix}-'"
            )

    # superseded_by must be real
    sby = art.frontmatter.get("superseded_by")
    if sby and isinstance(sby, str) and sby not in known_ids:
        errors.append(f"superseded_by refers to unknown artifact: {sby}")

    # supersedes must be real
    sup = art.frontmatter.get("supersedes")
    if sup and isinstance(sup, str) and sup not in known_ids:
        errors.append(f"supersedes refers to unknown artifact: {sup}")

    # Version-pinned references: every PRD-XXX / ARCH-XXX / ADR-XXX / TKT-XXX
    # appearing OUTSIDE of code fences must be pinned with @version, and the
    # bare ID must exist.
    # Strip fenced code blocks to avoid false positives in examples.
    body_no_fences = re.sub(r"```.*?```", "", art.body, flags=re.DOTALL)
    for m in REF_RE.finditer(body_no_fences):
        kind, num, _ver = m.group(1), m.group(2), m.group(3)
        ref_id = f"{kind}-{num}"
        if ref_id not in known_ids:
            errors.append(f"referenced artifact {ref_id} does not exist")

    # Detect unpinned references like `PRD-001 ` (no @version) — warn.
    bare_re = re.compile(r"\b(PRD|ARCH|ADR|TKT)-\d{3,}(?!@)")
    for m in bare_re.finditer(body_no_fences):
        # allow inside placeholder like "PRD-XXX"
        token = m.group(0)
        if "XXX" in token:
            continue
        # skip if it's the artifact's own id near top
        if token == art_id:
            continue
        errors.append(
            f"unpinned reference '{token}' — must be '{token}@X.Y.Z'"
        )

    return errors


def main() -> int:
    if not DOCS_ROOT.is_dir():
        print(f"docs/ not found at {DOCS_ROOT}", file=sys.stderr)
        return 2

    known_ids = collect_known_ids()
    total = 0
    failed = 0
    for md in sorted(DOCS_ROOT.rglob("*.md")):
        if md.name.startswith("TEMPLATE"):
            continue
        # skip README files at any level of docs/
        if md.name.lower() == "readme.md":
            continue
        try:
            art = load_artifact(md)
        except ValueError as e:
            print(f"[FAIL] {md.relative_to(REPO_ROOT)}: {e}")
            failed += 1
            total += 1
            continue
        if art is None:
            print(f"[FAIL] {md.relative_to(REPO_ROOT)}: missing YAML frontmatter")
            failed += 1
            total += 1
            continue
        errors = validate_artifact(art, known_ids)
        total += 1
        if errors:
            failed += 1
            print(f"[FAIL] {md.relative_to(REPO_ROOT)}")
            for e in errors:
                print(f"    - {e}")
        else:
            print(f"[ OK ] {md.relative_to(REPO_ROOT)}")

    print()
    print(f"validated {total} artifact(s); {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
