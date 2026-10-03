#!/usr/bin/env python3
"""Build focused OpenAI plugins from authored skills and verified library pins.

No network, credentials or live MCP operations are needed for a build.
Repin reads immutable git objects from the supplied, freshly fetched checkouts.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAGMENTS = ("workflow-loop.md", "delivery-rules.md")
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/"
GATEWAY = "https://gateway.ansvar.eu/mcp"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def read(path):
    if path.is_symlink():
        raise ValueError(f"Symlink is not a package source: {path}")
    return path.read_bytes()


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def upstream(wf_source, ai_source):
    ai_commit = git(ai_source, "rev-parse", "origin/main").decode().strip()
    pin = json.loads(git(ai_source, "show", f"{ai_commit}:scripts/workflow-skills.pin.json"))
    commit = pin["commit"]
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("Workflow pin is not a full commit")
    manifest_bytes = git(wf_source, "show", f"{commit}:instructions/dist/manifest.json")
    if digest(manifest_bytes) != pin["manifest_sha256"]:
        raise ValueError("Published workflow manifest does not match its pin")
    manifest = json.loads(manifest_bytes)
    indexed = {row["path"]: row["sha256"] for row in manifest["fragments"]}
    files = {}
    rows = []
    for name in FRAGMENTS:
        source = "instructions/dist/fragments/" + name
        data = git(wf_source, "show", f"{commit}:{source}")
        if digest(data) != indexed[source]:
            raise ValueError(f"Upstream fragment hash mismatch: {source}")
        target = "openai/vendor/" + name
        files[target] = data
        rows.append({"path": target, "source_path": source, "sha256": digest(data)})
    asset = "public/apple-touch-icon.png"
    icon = git(ai_source, "show", f"{ai_commit}:{asset}")
    files["openai/assets/icon.png"] = icon
    lock = {
        "workflow_repo": "Ansvar-Systems/ansvar-workflow-mcp",
        "workflow_commit": commit,
        "workflow_manifest_sha256": digest(manifest_bytes),
        "publication_repo": "Ansvar-Systems/ansvar-ai",
        "publication_commit": ai_commit,
        "fragments": rows,
        "icon": {"path": "openai/assets/icon.png", "source_path": asset, "sha256": digest(icon)},
    }
    return lock, files


def repin(root, wf_source, ai_source, check=False):
    lock, files = upstream(wf_source, ai_source)
    if check:
        existing = json.loads(read(root / "openai/upstream-lock.json"))
        # The website commit can move for unrelated work; compare the actual inputs.
        for key in ("workflow_commit", "workflow_manifest_sha256", "fragments", "icon"):
            if existing[key] != lock[key]:
                raise ValueError(f"Published input changed: {key}; review and repin")
        verify_inputs(root)
        return
    for path, data in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (root / "openai/upstream-lock.json").write_bytes(json_bytes(lock))


def verify_inputs(root):
    lock = json.loads(read(root / "openai/upstream-lock.json"))
    expected = {f"openai/vendor/{name}" for name in FRAGMENTS}
    if {r["path"] for r in lock["fragments"]} != expected:
        raise ValueError("Unexpected fragment roster")
    if lock["icon"]["path"] != "openai/assets/icon.png":
        raise ValueError("Unexpected branding source")
    for row in [*lock["fragments"], lock["icon"]]:
        if digest(read(root / row["path"])) != row["sha256"]:
            raise ValueError(f"Vendored input drift: {row['path']}")
    return lock


def validate_spec(spec):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", spec["id"]):
        raise ValueError("Invalid plugin id")
    for key in ("title", "subtitle"):
        if not 1 <= len(spec[key]) <= 30:
            raise ValueError(f"{spec['id']}: {key} must fit the listing's 30-character limit")
    if len(spec["description"]) > 4000:
        raise ValueError("Description exceeds listing limit")
    if len(spec["positive"]) != 5 or len(spec["negative"]) != 3:
        raise ValueError("Initial MCP review requires five positive and three negative cases")
    prompts = spec["prompts"] + [c["prompt"] for c in spec["positive"] + spec["negative"]]
    if any(not p.startswith(("Using Ansvar,", "Using Ansvar:")) for p in prompts):
        raise ValueError("Customer examples must lead with Using Ansvar")
    for case in spec["positive"]:
        if not case["tools_triggered"] or not case["expected_behavior"]:
            raise ValueError("Incomplete review case")
    for case in spec["negative"]:
        if not case["expected_behavior"]:
            raise ValueError("Negative case needs an observable outcome")


def package_files(root, spec, version, lock):
    validate_spec(spec)
    sid = spec["id"]
    prefix = f"skills/{sid}/"
    interface = {
        "displayName": spec["title"], "shortDescription": spec["subtitle"],
        "longDescription": spec["description"], "developerName": "Ansvar Systems AB",
        "category": "Productivity",
        "websiteURL": "https://ansvar.eu/docs/agent-skills",
        "supportURL": "https://ansvar.eu/contact",
        "privacyPolicyURL": "https://ansvar.eu/privacy",
        "termsOfServiceURL": "https://ansvar.eu/terms",
        "defaultPrompt": spec["prompts"], "brandColor": "#6355e6",
        "logo": "./assets/icon.png", "composerIcon": "./assets/icon.png",
    }
    manifest = {
        "$schema": SCHEMA + "plugin.schema.json",
        "name": sid, "version": version, "description": spec["summary"],
        "author": {"name": "Ansvar Systems AB", "email": "team@ansvar.eu", "url": "https://ansvar.eu"},
        "homepage": "https://ansvar.eu/docs/agent-skills",
        "repository": "https://github.com/Ansvar-Systems/ansvar-compliance-skills",
        "license": "CC-BY-4.0", "keywords": spec["keywords"],
        "extensions": {"com.openai": {
            "interface": interface,
            "review": {"test_cases": {"positive": spec["positive"], "negative": spec["negative"]},
                       "commerce": False},
            "publication": {"release_notes": "Initial focused workflow package using the Ansvar Gateway."},
        }},
    }
    files = {
        "plugin.json": json_bytes(manifest),
        "mcp.json": json_bytes({"$schema": SCHEMA + "mcp.schema.json", "mcpServers": {
            "ansvar": {"type": "streamable-http", "url": GATEWAY}}}),
        "assets/icon.png": read(root / "openai/assets/icon.png"),
        "LICENSE": read(root / "LICENSE"),
        "NOTICE": read(root / "openai/NOTICE"),
        "provenance.json": json_bytes({
            "workflow_commit": lock["workflow_commit"] if spec["workflow"] else None,
            "branding_commit": lock["publication_commit"],
            "source_license": "CC-BY-4.0",
        }),
        prefix + "SKILL.md": read(root / f"openai/src/{sid}/SKILL.md"),
        prefix + "references/grounding.md": read(root / "openai/shared/grounding.md"),
    }
    refdir = root / f"openai/src/{sid}/references"
    if refdir.exists():
        for path in sorted(refdir.iterdir()):
            if not path.is_file() or path.suffix != ".md":
                raise ValueError(f"Unexpected reference: {path}")
            files[prefix + "references/" + path.name] = read(path)
    if spec["workflow"]:
        for name in FRAGMENTS:
            files[prefix + "references/" + name] = read(root / "openai/vendor" / name)
    validate_files(files)
    return files


def validate_files(files):
    # All paths come from the explicit packaging allowlist above.
    for name in files:
        p = Path(name)
        if p.is_absolute() or ".." in p.parts or "\\" in name:
            raise ValueError(f"Unsafe archive path: {name}")
    icon = files["assets/icon.png"]
    if icon[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Brand icon is not PNG")
    width, height = struct.unpack(">II", icon[16:24])
    if width != height or not 48 <= width <= 4096 or len(icon) > 5 * 1024 * 1024:
        raise ValueError("Icon does not meet published dimensions/size limits")
    for name, content in files.items():
        if not name.endswith(".md"):
            continue
        body = content.decode()
        if name.endswith("SKILL.md"):
            if not body.startswith("---\n") or "\n---\n" not in body[4:]:
                raise ValueError(f"Missing skill frontmatter: {name}")
        for target in re.findall(r"\]\(([^ )]+)\)", body):
            if "://" in target or target.startswith("#"):
                continue
            resolved = str(Path(name).parent / target.split("#", 1)[0])
            if resolved not in files:
                raise ValueError(f"Missing packaged reference: {name} -> {target}")


def archive(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    return output.getvalue()


def build(root, output=None):
    lock = verify_inputs(root)
    catalog = json.loads(read(root / "openai/catalog.json"))
    if not re.fullmatch(r"\d+\.\d+\.\d+", catalog["version"]):
        raise ValueError("Version must be semantic")
    ids = [s["id"] for s in catalog["plugins"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate package ids")
    if set(ids) != {p.name for p in (root / "openai/src").iterdir() if p.is_dir()}:
        raise ValueError("Source skill roster differs from catalog")
    result = {}
    for spec in catalog["plugins"]:
        files = package_files(root, spec, catalog["version"], lock)
        data = archive(files)
        name = f"{spec['id']}-{catalog['version']}.zip"
        result[name] = data
    if output:
        output.mkdir(parents=True, exist_ok=True)
        for name, data in result.items():
            (output / name).write_bytes(data)
        (output / "checksums.json").write_bytes(json_bytes({n: digest(d) for n, d in result.items()}))
    return result


def verify_dist(root, output):
    expected = build(root)
    actual_names = {p.name for p in output.glob("*.zip")}
    if actual_names != set(expected):
        raise ValueError("Distribution archive roster differs from current catalog")
    for name, data in expected.items():
        if read(output / name) != data:
            raise ValueError(f"Distribution archive differs from source: {name}")
    checksums = json.loads(read(output / "checksums.json"))
    if checksums != {name: digest(data) for name, data in expected.items()}:
        raise ValueError("Distribution checksum manifest differs from source")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "check", "verify-dist", "repin", "check-upstream"])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--wf-source", type=Path)
    parser.add_argument("--ai-source", type=Path)
    args = parser.parse_args()
    if args.command in ("repin", "check-upstream"):
        if not args.wf_source or not args.ai_source:
            parser.error("repin/check-upstream requires both source checkouts")
        repin(args.root, args.wf_source, args.ai_source, check=args.command == "check-upstream")
    elif args.command == "verify-dist":
        verify_dist(args.root, args.output or args.root / "openai/dist")
    else:
        output = (args.output or args.root / "openai/dist") if args.command == "build" else None
        packages = build(args.root, output)
        for name, data in packages.items():
            print(f"{name}: {len(data)} bytes sha256={digest(data)}")
    print("PASS")


if __name__ == "__main__":
    main()
