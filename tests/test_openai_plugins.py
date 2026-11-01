"""Packaging contract tests; no live credentials or MCP writes."""
import copy
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("openai_plugins", ROOT / "scripts/openai_plugins.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class Packages(unittest.TestCase):
    def test_compiled_adaptation_and_source_tampering_refuse(self):
        for path in ("openai/vendor/vulnerability-management.md",
                     "openai/src/ansvar-vulnerability-management/SKILL.md",
                     "openai/vendor/zero-trust.md",
                     "openai/src/ansvar-zero-trust/SKILL.md",
                     "openai/vendor/cmmc.md",
                     "openai/src/ansvar-cmmc/SKILL.md"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                shutil.copytree(ROOT / "openai", root / "openai", ignore=shutil.ignore_patterns("dist"))
                (root / path).write_text("tampered")
                with self.assertRaisesRegex(ValueError, "drift"):
                    builder.verify_inputs(root)

    def test_compiled_adapter_requires_review_on_upstream_change(self):
        compiled = (ROOT / "openai/vendor/vulnerability-management.md").read_bytes()
        with self.assertRaisesRegex(ValueError, "adapter needs review"):
            builder.adapt_compiled(compiled.replace(b"At Premium or above", b"When authorized"))
        adapted = builder.adapt_compiled(compiled).decode()
        self.assertNotRegex(adapted, r"\b(?:Premium|Solo|Free|upgrade)\b")
        for contract in ("scanner findings", "cursor_expired", "snapshot_required",
                         "baseline_report_id", "Unknown basis cannot close a gap"):
            self.assertIn(contract, adapted)

    def test_zero_trust_contract_and_commercial_adapter(self):
        compiled = (ROOT / "openai/vendor/zero-trust.md").read_bytes()
        with self.assertRaisesRegex(ValueError, "adapter needs review"):
            builder.adapt_compiled(compiled.replace(b"Free and Solo include one and two assessment", b"Accounts include"),
                                   "ansvar-zero-trust")
        adapted = builder.adapt_compiled(compiled, "ansvar-zero-trust").decode()
        self.assertNotRegex(adapted, r"\b(?:Premium|Solo|Free|Team|Company|upgrade)\b")
        self.assertNotIn("tier_caveat", adapted)
        for contract in ("never submit it to a step", "baseline_report_id",
                         "fetched crosswalk rows", "never map controls", "related-to",
                         "interview_attestation", "Unknown evidence requires",
                         "guidance and practice references", "self-assessment",
                         "wait for an actual answer", "does not establish a stage"):
            self.assertIn(contract, adapted)
        catalog = json.loads((ROOT / "openai/catalog.json").read_text())
        self.assertEqual(catalog["version"], "0.5.0")
        self.assertEqual(len(catalog["plugins"]), 6)
        item = next(p for p in catalog["plugins"] if p["id"] == "ansvar-zero-trust")
        self.assertTrue(all(len(p) <= 128 for p in item["prompts"]))
        broken = copy.deepcopy(item)
        broken["prompts"][0] = "Using Ansvar, " + "x" * 128
        with self.assertRaisesRegex(ValueError, "submission limit"):
            builder.validate_spec(broken)
        self.assertEqual(len(builder.verify_inputs(ROOT)["compiled_skills"]), 3)

    def test_cmmc_contract_and_commercial_adapter(self):
        compiled = (ROOT / "openai/vendor/cmmc.md").read_bytes()
        with self.assertRaisesRegex(ValueError, "adapter needs review"):
            builder.adapt_compiled(compiled.replace(b"on free and solo the gateway", b"the gateway"),
                                   "ansvar-cmmc")
        adapted = builder.adapt_compiled(compiled, "ansvar-cmmc").decode()
        # "red-team" and the "tier" response field are not commercial wording.
        self.assertNotRegex(adapted, r"(?i)(?<![-\w\"])(?:premium|solo|free|team|company|upgrade|tiers?)\b")
        for contract in ("cmmc_l1_self", "cmmc_l2_self", "closeout_of", "32 CFR 170.24",
                         "out of 110", "15 requirements", "Never submit a score",
                         "self-assessment aid", "as a C3PAO assessment",
                         "never give the affirmation for the person"):
            self.assertIn(contract, adapted)
        catalog = json.loads((ROOT / "openai/catalog.json").read_text())
        item = next(p for p in catalog["plugins"] if p["id"] == "ansvar-cmmc")
        self.assertTrue(all(len(p) <= 128 for p in item["prompts"]))
        listing = " ".join([item["description"], item["summary"], item["subtitle"]])
        self.assertNotRegex(listing, r"(?i)\b(?:premium|solo|free|team|company|upgrade|plan|pricing|checkout)\b")
        self.assertIn("not a C3PAO assessment", item["description"])

    def test_compiled_archives_carry_no_commercial_wording(self):
        catalog = json.loads((ROOT / "openai/catalog.json").read_text())
        lock = builder.verify_inputs(ROOT)
        for spec in catalog["plugins"]:
            if spec["id"] not in builder.COMPILED_IDS:
                continue
            files = builder.package_files(ROOT, spec, catalog["version"], lock)
            for name in builder.FRAGMENTS:
                self.assertNotIn(f"skills/{spec['id']}/references/{name}", files)
            for name, data in files.items():
                if name.endswith(".md") and not name.endswith("grounding.md"):
                    with self.subTest(package=spec["id"], file=name):
                        self.assertNotRegex(data.decode(),
                                            r"(?i)(?<![-\w\"])(?:premium|solo|free|team|company|upgrade|tiers?)\b(?!-)")

    def test_reproducible_and_self_contained(self):
        first = builder.build(ROOT)
        self.assertEqual(first, builder.build(ROOT))
        for raw in first.values():
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                self.assertIsNone(z.testzip())
                manifest = json.loads(z.read("plugin.json"))
                mcp = json.loads(z.read("mcp.json"))
                self.assertEqual(mcp["mcpServers"], {
                    "ansvar": {"type": "streamable-http", "url": builder.GATEWAY}})
                self.assertNotIn("apps", manifest)
                self.assertNotIn("hooks", manifest)
                self.assertFalse(any(n.startswith(".git") for n in z.namelist()))
                prefix = "skills/" + manifest["name"] + "/"
                self.assertIn(prefix + "SKILL.md", z.namelist())
                self.assertIn(prefix + "references/grounding.md", z.namelist())
                builder.validate_files({n: z.read(n) for n in z.namelist()})
                cases = manifest["extensions"]["com.openai"]["review"]["test_cases"]
                self.assertEqual((len(cases["positive"]), len(cases["negative"])), (5, 3))

    def test_tampered_fragment_refuses_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "openai", root / "openai", ignore=shutil.ignore_patterns("dist"))
            shutil.copy(ROOT / "LICENSE", root / "LICENSE")
            (root / "openai/vendor/workflow-loop.md").write_text("tampered")
            with self.assertRaisesRegex(ValueError, "Vendored input drift"):
                builder.build(root)

    def test_stale_or_tampered_distribution_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            packages = builder.build(ROOT, output)
            builder.verify_dist(ROOT, output)
            name = next(iter(packages))
            (output / name).write_bytes(b"stale or tampered")
            with self.assertRaisesRegex(ValueError, "differs from source"):
                builder.verify_dist(ROOT, output)
            builder.build(ROOT, output)
            (output / "unexpected.zip").write_bytes(b"unexpected")
            with self.assertRaisesRegex(ValueError, "roster differs"):
                builder.verify_dist(ROOT, output)

    def test_missing_reference_refuses_package(self):
        config = json.loads((ROOT / "openai/catalog.json").read_text())
        item = config["plugins"][0]
        files = builder.package_files(ROOT, item, config["version"], builder.verify_inputs(ROOT))
        del files["skills/" + item["id"] + "/references/grounding.md"]
        with self.assertRaisesRegex(ValueError, "Missing packaged reference"):
            builder.validate_files(files)

    def test_missing_review_case_and_long_listing_refuse(self):
        item = json.loads((ROOT / "openai/catalog.json").read_text())["plugins"][0]
        broken = copy.deepcopy(item)
        broken["positive"].pop()
        with self.assertRaisesRegex(ValueError, "five positive"):
            builder.validate_spec(broken)
        broken = copy.deepcopy(item)
        broken["subtitle"] = "x" * 31
        with self.assertRaisesRegex(ValueError, "30-character"):
            builder.validate_spec(broken)

    def test_symlink_input_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "skill.md"
            p.symlink_to(ROOT / "openai/shared/grounding.md")
            with self.assertRaisesRegex(ValueError, "Symlink"):
                builder.read(p)

    def test_duplicate_catalog_id_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "openai", root / "openai", ignore=shutil.ignore_patterns("dist"))
            shutil.copy(ROOT / "LICENSE", root / "LICENSE")
            p = root / "openai/catalog.json"
            catalog = json.loads(p.read_text())
            catalog["plugins"].append(catalog["plugins"][0])
            p.write_text(json.dumps(catalog))
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                builder.build(root)


if __name__ == "__main__":
    unittest.main()
