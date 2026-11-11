#!/usr/bin/env python3
#
# Validate the Yugen repo manifest: well-formedness, no duplicate project
# paths, every remote resolvable, and every remove-project actually matching
# something.
#
# Projects and removals are processed in include order, the way `repo` does it.
#
# SPDX-License-Identifier: Apache-2.0
#
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(path: Path, seen: set[Path], projects: list[ET.Element],
         remotes: dict[str, str], removed: list[str], warnings: list[str]) -> None:
    """Walk one manifest file, applying projects/remotes/removals in order."""
    if path in seen:
        sys.exit(f"include cycle: {path}")
    seen.add(path)

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        # The usual cause is a "--" inside a comment, which XML forbids.
        sys.exit(f"{path.relative_to(ROOT)}: {exc}\n"
                 "hint: '--' may not appear inside an XML comment")
    for node in tree.getroot():
        if node.tag == "remote":
            remotes[node.get("name")] = node.get("fetch")
        elif node.tag == "project":
            projects.append(node)
        elif node.tag == "remove-project":
            name = node.get("name")
            match = [p for p in projects if p.get("name") == name]
            if not match:
                warnings.append(f"{path.name}: remove-project {name} matches nothing")
            projects[:] = [p for p in projects if p.get("name") != name]
            removed.append(name)
        elif node.tag == "include":
            sub = ROOT / node.get("name")
            if not sub.exists():
                sys.exit(f"missing include: {sub}")
            load(sub, seen, projects, remotes, removed, warnings)


def main() -> int:
    projects: list[ET.Element] = []
    remotes: dict[str, str] = {}
    removed: list[str] = []
    warnings: list[str] = []

    load(ROOT / "default.xml", set(), projects, remotes, removed, warnings)

    errors: list[str] = []
    paths: dict[str, str] = {}

    for p in projects:
        path, name = p.get("path"), p.get("name")
        if not path or not name:
            errors.append(f"project missing path/name: {ET.tostring(p, 'unicode').strip()}")
            continue
        if path in paths:
            errors.append(f"duplicate path {path}: {paths[path]} vs {name}")
        paths[path] = name

        remote = p.get("remote")
        if remote and remote not in remotes:
            errors.append(f"{path}: unknown remote '{remote}'")

    if "aosp" not in remotes:
        errors.append("no 'aosp' remote defined")

    for w in warnings:
        print(f"warning: {w}")
    for err in errors:
        print(f"error: {err}")
    if errors:
        return 1

    print(f"ok: {len(projects)} projects, {len(remotes)} remotes, "
          f"{len(removed)} removals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
