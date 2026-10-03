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
