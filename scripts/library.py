#!/usr/bin/env python3
"""Vendor and verify the workflow skill library (called by scripts/sync.sh).

The library skills come from two PRIVATE repositories:

* the family skills, compiled in Ansvar-Systems/ansvar-workflow-mcp under
  instructions/dist/, listed with a sha256 per artifact in
  instructions/dist/manifest.json;
* using-ansvar, hand-published by Ansvar-Systems/ansvar-ai at
  public/skills/using-ansvar/SKILL.md.

ansvar-ai is the checksummed consumer that publishes all of them on ansvar.eu.
This plugin follows the same pin: `repin` reads ansvar-ai's
scripts/workflow-skills.pin.json (wf-mcp commit + manifest sha256) and copies
the exact bytes at that commit. The family list comes from the upstream
manifest, never from a hand-written list in this repository.

  check  offline hash check of every vendored library file against
         skills-manifest.json, a sweep for unlisted skill directories, then a
         comparison with the public copy on ansvar.eu.
  repin  refresh from local checkouts of both private repositories.

Standard library only; bytes are read with `git show <commit>:<path>`, never
from a working tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

MANIFEST_NAME = "skills-manifest.json"
WF_REPO = "Ansvar-Systems/ansvar-workflow-mcp"
AI_REPO = "Ansvar-Systems/ansvar-ai"
UPSTREAM_MANIFEST = "instructions/dist/manifest.json"
AI_PIN = "scripts/workflow-skills.pin.json"
AI_VENDORED_MANIFEST = "src/data/workflow-skills.manifest.json"
# The one library skill that is not a compiled family. It is named here
# because it is hand-published and appears in no upstream manifest.
HAND_PUBLISHED = {"using-ansvar": "public/skills/using-ansvar/SKILL.md"}
PUBLISHED_URL = "https://ansvar.eu/skills/{id}/SKILL.md"
# Skill directories that scripts/sync.sh raw-fetches from their own public
# repositories. Keep in step with MAPPINGS in scripts/sync.sh.
STANDALONE = {
    "regulatory-threat-model",
    "incident-reporting-navigator",
    "cra-vulnerability-obligations",
    "iso-standards-expert",
}


ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def valid_id(sid: object) -> bool:
    return isinstance(sid, str) and bool(ID_RE.fullmatch(sid))


def write_atomic(path: Path, data: bytes) -> None:
    """Write via a temp file in the same directory, then rename: a crash leaves
    either the old file or the new one, never a partial file."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def symlinks_under(skills_dir: Path) -> list[str]:
    """Every symlink in skills/, dangling or not. Vendored content is plain
    files only; a link could point a write or a check outside the repo."""
    found = []
    for dirpath, dirnames, filenames in os.walk(skills_dir, followlinks=False):
        for name in dirnames + filenames:
            full = Path(dirpath) / name
            if full.is_symlink():
                found.append(str(full.relative_to(skills_dir.parent)))
    return sorted(found)


def fail(msg: str) -> None:
    print(f"library: ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(source: Path, *args: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "-C", str(source), *args],
            check=True,
            capture_output=True,
        ).stdout
    except subprocess.CalledProcessError as err:
        fail(f"git -C {source} {' '.join(args)}: {err.stderr.decode().strip()}")
    raise AssertionError  # unreachable


def show(source: Path, commit: str, path: str) -> bytes:
    return git(source, "show", f"{commit}:{path}")


# --------------------------------------------------------------------- check


def cmd_check(root: Path) -> int:
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        fail(f"{MANIFEST_NAME} is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("skills") or []
    if not entries:
        fail(f"{MANIFEST_NAME} lists no skills")

    problems: list[str] = [f"{p}: symlink (not allowed under skills/)" for p in symlinks_under(root / "skills")]
    ids = set()
    for entry in entries:
        sid = entry.get("id", "")
        if not valid_id(sid):
            problems.append(f"unusable skill id {sid!r}")
            continue
        if sid in ids:
            problems.append(f"duplicate skill id {sid!r}")
            continue
        ids.add(sid)
        rel = entry.get("path", "")
        if rel != f"skills/{sid}/SKILL.md":
            problems.append(f"{sid}: path {rel!r} is not skills/{sid}/SKILL.md")
            continue
        target = root / rel
        if not target.is_file():
            problems.append(f"{rel}: missing")
            continue
        actual = sha256(target.read_bytes())
        if actual != entry.get("sha256"):
            problems.append(f"{rel}: sha256 {actual} != manifest {entry.get('sha256')}")
        strays = [p.name for p in target.parent.iterdir() if p.name != "SKILL.md"]
        if strays:
            problems.append(f"skills/{sid}/: unlisted file(s) {', '.join(sorted(strays))}")

    overlap = ids & STANDALONE
    if overlap:
        problems.append(f"id(s) in both lanes: {', '.join(sorted(overlap))}")
    on_disk = {p.name for p in (root / "skills").iterdir() if p.is_dir()}
    unclaimed = on_disk - ids - STANDALONE
    if unclaimed:
        problems.append(
            "skills/ directories in neither lane: " + ", ".join(sorted(unclaimed))
        )

    if problems:
        print(f"DRIFT DETECTED: library integrity ({len(problems)}):")
        for p in problems:
            print(f"  {p}")
        return 1
    wf = manifest.get("workflow_library", {})
    print(
        f"OK: {len(entries)} library skills match {MANIFEST_NAME} "
        f"({WF_REPO}@{str(wf.get('commit', '?'))[:12]}, "
        f"bundle {wf.get('content_bundle_version', '?')})"
    )

    # Currency: ansvar.eu publishes the same pin. A difference there means
    # ansvar-ai re-pinned and this plugin has not followed yet.
    stale = 0
    for entry in entries:
        if not valid_id(entry.get("id")):
            continue
        url = PUBLISHED_URL.format(id=entry["id"])
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "ansvar-compliance-skills-anti-drift"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status != 200 or resp.geturl() != url:
                    print(f"ERROR: {url} answered {resp.status} at {resp.geturl()}, expected 200 with no redirect")
                    stale += 1
                    continue
                published = resp.read()
        except (urllib.error.URLError, TimeoutError) as err:
            print(f"ERROR: failed to fetch {url}: {err}")
            stale += 1
            continue
        if sha256(published) != entry["sha256"]:
            print(
                f"DRIFT DETECTED: {entry['path']} differs from {url} "
                f"(published {sha256(published)[:12]}, vendored {entry['sha256'][:12]}); "
                "run scripts/sync.sh --repin"
            )
            stale += 1
        else:
            print(f"OK: {entry['path']} matches {url}")
    return 1 if stale else 0


# --------------------------------------------------------------------- repin


def cmd_repin(root: Path, wf_source: Path, ai_source: Path, ai_ref: str) -> int:
    ai_commit = git(ai_source, "rev-parse", "--verify", f"{ai_ref}^{{commit}}").decode().strip()
    pin = json.loads(show(ai_source, ai_commit, AI_PIN))
    for field in ("repo", "commit", "manifest_sha256"):
        if not pin.get(field):
            fail(f"{AI_REPO}@{ai_commit[:12]}:{AI_PIN} has no {field!r}")
    if pin["repo"] != WF_REPO:
        fail(f"pin names {pin['repo']!r}, expected {WF_REPO!r}")
    wf_commit = pin["commit"]
    git(wf_source, "cat-file", "-e", f"{wf_commit}^{{commit}}")

    manifest_bytes = show(wf_source, wf_commit, UPSTREAM_MANIFEST)
    if sha256(manifest_bytes) != pin["manifest_sha256"]:
        fail(
            f"{UPSTREAM_MANIFEST} at {wf_commit[:12]} hashes to {sha256(manifest_bytes)}, "
            f"pin says {pin['manifest_sha256']}"
        )
    # ansvar-ai vendors the same manifest; it must be the pinned one.
    ai_vendored = show(ai_source, ai_commit, AI_VENDORED_MANIFEST)
    if sha256(ai_vendored) != pin["manifest_sha256"]:
        fail(f"{AI_REPO}@{ai_commit[:12]}:{AI_VENDORED_MANIFEST} does not match its own pin")
    upstream = json.loads(manifest_bytes)
    families = upstream.get("families") or []
    if not families:
        fail("upstream manifest lists no families")

    payload: list[tuple[dict, bytes]] = []
    seen: set[str] = set()
    for fam in families:
        fid = fam.get("id", "")
        if not valid_id(fid):
            fail(f"unusable family id {fid!r}")
        if fid in seen:
            fail(f"duplicate family id {fid!r} in the upstream manifest")
        seen.add(fid)
        if fid in STANDALONE or fid in HAND_PUBLISHED:
            fail(f"family {fid!r} collides with a skill vendored by another lane")
        path = f"instructions/dist/{fid}/SKILL.md"
        art = next((a for a in fam.get("artifacts", []) if a.get("path") == path), None)
        if art is None:
            fail(f"family {fid!r} has no artifact {path}")
        data = show(wf_source, wf_commit, path)
        if sha256(data) != art.get("sha256"):
            fail(f"{path} at {wf_commit[:12]} does not match the manifest sha256")
        # The published copy on ansvar.eu comes from the same bytes.
        ai_copy = show(ai_source, ai_commit, f"public/skills/{fid}/SKILL.md")
        if ai_copy != data:
            fail(f"{AI_REPO}@{ai_commit[:12]}:public/skills/{fid}/SKILL.md differs from the pinned artifact")
        payload.append(
            (
                {
                    "id": fid,
                    "lane": "workflow-family",
                    "title": fam.get("title"),
                    "instruction_version": fam.get("instruction_version"),
                    "path": f"skills/{fid}/SKILL.md",
                    "sha256": art["sha256"],
                    "source": {"repo": WF_REPO, "commit": wf_commit, "path": path},
                },
                data,
            )
        )

    for sid, path in HAND_PUBLISHED.items():
        data = show(ai_source, ai_commit, path)
        payload.append(
            (
                {
                    "id": sid,
                    "lane": "hand-published",
                    "path": f"skills/{sid}/SKILL.md",
                    "sha256": sha256(data),
                    "source": {"repo": AI_REPO, "commit": ai_commit, "path": path},
                },
                data,
            )
        )

    links = symlinks_under(root / "skills")
    if links:
        fail("symlinks under skills/ (remove them first): " + ", ".join(links))

    manifest_path = root / MANIFEST_NAME
    previous: set[str] = set()
    if manifest_path.is_file():
        for e in json.loads(manifest_path.read_text(encoding="utf-8")).get("skills", []):
            sid = e.get("id")
            # Ids read back from disk decide what gets deleted: validate them
            # before any mutation, same as incoming ids.
            if not valid_id(sid) or sid in STANDALONE:
                fail(f"{MANIFEST_NAME} lists unusable or foreign id {sid!r}; restore it from git")
            previous.add(sid)
    current = {entry["id"] for entry, _ in payload}

    # A new id may not land on a directory this lane did not own before. The
    # one exception is a leftover of an interrupted repin: a directory that
    # holds only SKILL.md with exactly the bytes about to be written.
    wanted = {entry["id"]: data for entry, data in payload}
    for sid in sorted(current - previous):
        d = root / "skills" / sid
        if not d.exists():
            continue
        names = sorted(p.name for p in d.iterdir()) if d.is_dir() else []
        if names == ["SKILL.md"] and (d / "SKILL.md").read_bytes() == wanted[sid]:
            print(f"  adopting skills/{sid} (left by an interrupted repin, bytes match)")
            continue
        fail(f"refusing to adopt skills/{sid}: it exists and is not in {MANIFEST_NAME}")

    # Order: write files, prune, then the manifest. A failure before the
    # manifest write leaves the old manifest in place, so the next run still
    # owns (and retries pruning) every previously listed id.
    for entry, data in payload:
        target = root / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or target.read_bytes() != data:
            write_atomic(target, data)
            print(f"  wrote {entry['path']}")

    for sid in sorted(previous - current):
        d = root / "skills" / sid
        if d.exists():
            shutil.rmtree(d)  # raises on failure; the manifest is not rewritten
            print(f"  - skills/{sid} (no longer published)")

    out = {
        "schema": 1,
        "generated_by": "scripts/sync.sh --repin",
        "workflow_library": {
            "repo": WF_REPO,
            "commit": wf_commit,
            "manifest_path": UPSTREAM_MANIFEST,
            "manifest_sha256": pin["manifest_sha256"],
            "content_bundle_version": (
                upstream.get("build_identity", {}).get("content_bundle", {}).get("version_label")
            ),
            "pinned_by": {"repo": AI_REPO, "commit": ai_commit, "path": AI_PIN},
        },
        "published_at": PUBLISHED_URL,
        "skills": sorted((entry for entry, _ in payload), key=lambda e: e["id"]),
    }
    text = json.dumps(out, indent=2, ensure_ascii=False) + "\n"
    if not manifest_path.is_file() or manifest_path.read_text(encoding="utf-8") != text:
        write_atomic(manifest_path, text.encode("utf-8"))
        print(f"  wrote {MANIFEST_NAME}")
    print(
        f"library: {len(payload)} skills from {WF_REPO}@{wf_commit[:12]} "
        f"and {AI_REPO}@{ai_commit[:12]}"
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--root", type=Path, required=True)
    r = sub.add_parser("repin")
    r.add_argument("--root", type=Path, required=True)
    r.add_argument("--wf-source", type=Path, required=True)
    r.add_argument("--ai-source", type=Path, required=True)
    r.add_argument("--ai-ref", default="origin/main")
    a = ap.parse_args()
    if a.cmd == "check":
        return cmd_check(a.root.resolve())
    return cmd_repin(a.root.resolve(), a.wf_source.resolve(), a.ai_source.resolve(), a.ai_ref)


if __name__ == "__main__":
    sys.exit(main())
