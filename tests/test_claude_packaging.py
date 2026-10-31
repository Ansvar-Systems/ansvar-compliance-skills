"""Release constraints for the bundle and focused Claude package."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ClaudePackaging(unittest.TestCase):
    def test_manifest_roster_and_focused_copies(self):
        manifest = json.loads((ROOT / 'skills-manifest.json').read_text())
        marketplace = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        self.assertEqual(len(list((ROOT / 'skills').glob('*/SKILL.md'))), 17)
        self.assertIn('zero-trust', {s['id'] for s in manifest['skills']})
        self.assertEqual(manifest['workflow_library']['commit'],
                         '2d23495b8c999539e6dc69d368fb258f9a482ede')
        for entry in manifest['skills']:
            self.assertEqual(hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest(),
                             entry['sha256'])
        self.assertEqual({p['name'] for p in marketplace['plugins']},
                         {'ansvar-compliance-skills', 'ansvar-vulnerability-management'})
        focused = ROOT / 'plugins/ansvar-vulnerability-management'
        self.assertEqual({p.name for p in (focused / 'skills').iterdir()},
                         {'using-ansvar', 'vulnerability-management'})
        for sid in ('using-ansvar', 'vulnerability-management'):
            rel = f'skills/{sid}/SKILL.md'
            self.assertEqual((focused / rel).read_bytes(), (ROOT / rel).read_bytes())
        self.assertEqual((focused / '.mcp.json').read_bytes(), (ROOT / '.mcp.json').read_bytes())
        for base in (ROOT, focused):
            self.assertEqual(json.loads((base / '.claude-plugin/plugin.json').read_text())['version'],
                             '2.2.0')


if __name__ == '__main__':
    unittest.main()
