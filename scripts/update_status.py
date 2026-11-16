#!/usr/bin/env python3
"""
Regenerate the "Where the work stands" table in README.md from live GitHub state.

The README is hand-written, but its status table is a *frame* of the projects,
and a hand-maintained frame goes stale the moment you commit. This script
rewrites the table between the marker comments from the GitHub API, so it can
never drift from reality.

Everything is fetched in a SINGLE GraphQL request (the REST API costs ~11s per
call here; one query returns every repo's visibility and HEAD commit date).

Usage:  python3 scripts/update_status.py [--commit]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "projects.json"
README = ROOT / "README.md"

BEGIN = "<!-- STATUS:BEGIN -->"
END = "<!-- STATUS:END -->"

FIELDS = """
  name
  visibility
  pushedAt
  defaultBranchRef { target { ... on Commit { committedDate } } }
"""


def fetch_all(manifest: dict) -> dict:
    """One GraphQL query for every repo in the manifest."""
    parts = []
    for i, p in enumerate(manifest["projects"]):
        owner = p.get("owner", manifest["owner"])
        parts.append(
            f'  r{i}: repository(owner: "{owner}", name: "{p["repo"]}") {{ {FIELDS} }}'
        )
    query = "query {\n" + "\n".join(parts) + "\n}"
    out = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True, text=True, timeout=120, check=True,
    ).stdout
    data = json.loads(out).get("data", {})
    result = {}
    for i, p in enumerate(manifest["projects"]):
        node = data.get(f"r{i}")
        if node:
            result[p["key"]] = node
    return result


def fmt_date(node: dict) -> str:
    raw = (
        (node.get("defaultBranchRef") or {}).get("target", {}).get("committedDate")
        or node.get("pushedAt")
    )
    if not raw:
        return "—"
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    return dt.strftime("%d %b %Y")


def build_table(manifest: dict, live: dict) -> str:
    rows = [
        "| Project | What it is | State | Last commit | Access |",
        "|---|---|---|---|---|",
    ]
    for p in manifest["projects"]:
        node = live.get(p["key"])
        if node:
            vis = {"PUBLIC": "public", "PRIVATE": "private"}.get(
                node.get("visibility", ""), (node.get("visibility") or "").lower()
            )
            date = fmt_date(node)
        else:
            vis, date = "—", "—"
        rows.append(f"| **{p['name']}** | {p['what']} | {p['state']} | {date} | {vis} |")
    return "\n".join(rows)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    text = README.read_text()
    if BEGIN not in text or END not in text:
        print("markers not found in README.md", file=sys.stderr)
        return 1
    try:
        live = fetch_all(manifest)
    except Exception as exc:  # keep the README intact if the network/API fails
        print(f"could not reach GitHub ({exc}); leaving README untouched", file=sys.stderr)
        return 2
    table = build_table(manifest, live)
    new = re.sub(
        re.escape(BEGIN) + r".*?" + re.escape(END),
        f"{BEGIN}\n{table}\n{END}",
        text,
        flags=re.S,
    )
    if new == text:
        print("status table already current")
        return 0
    README.write_text(new)
    print("status table regenerated")
    if "--commit" in sys.argv:
        subprocess.run(["git", "add", "README.md", "projects.json"], cwd=ROOT, check=True)
        subprocess.run(
            ["git", "commit", "-m", "chore: regenerate project status table from live repo state"],
            cwd=ROOT, check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
