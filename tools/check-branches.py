#!/usr/bin/env python3
#
# Check that every project branch a snippet pins actually exists upstream.
#
#   ./tools/check-branches.py
#
# `repo sync` fails the whole run when a single project cannot resolve its
# revision, and the message ("couldn't find remote ref") does not say which
# branch would have worked. This catches that before a sync is started, and
# suggests the newest branch when a pin is stale.
#
# Network access required. Checks the LineageOS hardware snippet; AOSP projects
# are pinned to a tag, and the two vendor projects live in our own org.
#
# SPDX-License-Identifier: Apache-2.0
#
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKERS = 8


def load(path: Path) -> list[dict[str, str]]:
    return [dict(node.attrib) for node in ET.parse(path).getroot()
            if node.tag == "project"]


def load_remotes() -> dict[str, dict[str, str]]:
    return {node.get("name"): dict(node.attrib)
            for node in ET.parse(ROOT / "snippets/remote.xml").getroot()
            if node.tag == "remote"}


def heads(url: str) -> list[str]:
    out = subprocess.run(
        ["git", "ls-remote", "--heads", url],
        capture_output=True, text=True, timeout=120,
    )
    if out.returncode != 0:
        return []
    return [line.split("refs/heads/", 1)[1] for line in out.stdout.splitlines()
            if "refs/heads/" in line]


def check(item: tuple[dict[str, str], str, str]) -> str | None:
    project, revision, url = item
    branch = revision.replace("refs/heads/", "")

    available = heads(url)
    if branch in available:
        return None

    lineage = sorted(b for b in available if re.match(r"lineage-\d", b))
    hint = lineage[-1] if lineage else "no lineage-* branch"
    return (f"{project['path']}: branch {branch} not found in "
            f"{project['name']} (newest: {hint})")


def main() -> int:
    remotes = load_remotes()
    work: list[tuple[dict[str, str], str, str]] = []

    for project in load(ROOT / "snippets/external.xml"):
        remote = remotes.get(project.get("remote"))
        if remote is None:
            sys.exit(f"unknown remote on {project['path']}: {project.get('remote')}")
        revision = project.get("revision") or remote.get("revision")
        if revision is None:
            sys.exit(f"no revision for {project['path']}")
        url = f"{remote['fetch'].rstrip('/')}/{project['name']}"
        work.append((project, revision, url))

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        failures = [r for r in pool.map(check, work) if r]

    for failure in failures:
        print(f"error: {failure}")
    if failures:
        return 1

    print(f"ok: all {len(work)} snippet branches resolve upstream")
    return 0


if __name__ == "__main__":
    sys.exit(main())
