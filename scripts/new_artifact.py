#!/usr/bin/env python3
"""Scaffold a new artifact from a TEMPLATE.md with the next free ID.

Usage:
    python scripts/new_artifact.py <type> "<title>"

Types: prd | arch | adr | ticket | review-spec | review-code | question
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs"

TYPE_CONFIG = {
    "prd":         ("prd",               "PRD",       "TEMPLATE.md"),
    "arch":        ("architecture",      "ARCH",      "TEMPLATE.md"),
    "adr":         ("architecture/adr",  "ADR",       "TEMPLATE.md"),
    "ticket":      ("tickets",           "TKT",       "TEMPLATE.md"),
    "review-spec": ("reviews",           "RV-SPEC",   "TEMPLATE-spec.md"),
    "review-code": ("reviews",           "RV-CODE",   "TEMPLATE-code.md"),
    "question":    ("questions",         "Q",         "TEMPLATE.md"),
}


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip().lower()).strip("-")
    return slug or "untitled"


def next_id(dir_: Path, prefix: str) -> str:
    existing = []
    pat = re.compile(rf"^{re.escape(prefix)}-(\d{{3,}})")
    for f in dir_.glob("*.md"):
        if f.name.startswith("TEMPLATE"):
            continue
        m = pat.match(f.name)
        if m:
            existing.append(int(m.group(1)))
    next_num = (max(existing) + 1) if existing else 1
    return f"{prefix}-{next_num:03d}"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    type_key = argv[0]
    title = argv[1]
    cfg = TYPE_CONFIG.get(type_key)
    if cfg is None:
        print(f"unknown type '{type_key}'. options: {list(TYPE_CONFIG)}")
        return 2
    subdir, prefix, template_name = cfg
    dir_ = DOCS_ROOT / subdir
    dir_.mkdir(parents=True, exist_ok=True)
    template = dir_ / template_name
    if not template.exists():
        print(f"template not found: {template}")
        return 2
    new_id = next_id(dir_, prefix)
    slug = slugify(title)
    out_path = dir_ / f"{new_id}-{slug}.md"
    if out_path.exists():
        print(f"already exists: {out_path}")
        return 2

    today = dt.date.today().isoformat()
    content = template.read_text(encoding="utf-8")
    # basic substitutions
    content = content.replace(f"{prefix}-XXX", new_id)
    content = content.replace('title: ""', f'title: "{title}"')
    content = content.replace("YYYY-MM-DD", today)
    out_path.write_text(content, encoding="utf-8")
    print(f"created: {out_path.relative_to(REPO_ROOT)}")
    print(f"id: {new_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
