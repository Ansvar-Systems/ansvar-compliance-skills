"""Release constraints for the bundle and focused Claude package."""
import hashlib
import json
import unittest
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ClaudePackaging(unittest.TestCase):
    def test_manifest_roster_and_focused_copies(self):
        manifest = json.loads((ROOT / 'skills-manifest.json').read_text())
        marketplace = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        self.assertEqual(len(list((ROOT / 'skills').glob('*/SKILL.md'))), 20)
        self.assertIn('zero-trust', {s['id'] for s in manifest['skills']})
        self.assertEqual(manifest['workflow_library']['commit'],
                         'b825299b071b134b780f9d86fa9bca76585da763')
        for entry in manifest['skills']:
            self.assertEqual(hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest(),
                             entry['sha256'])
        self.assertEqual(len(manifest['skills']), 16)
        self.assertTrue({'zero-trust', 'cmmc', 'cmmc-level-1', 'cmmc-level-2'} <=
                        {s['id'] for s in manifest['skills']})
        self.assertEqual(marketplace['metadata']['version'], '2.5.0')
        self.assertEqual({p['name'] for p in marketplace['plugins']},
                         {'ansvar-compliance-skills', 'ansvar-vulnerability-management',
                          'ansvar-zero-trust', 'ansvar-cmmc'})
        bases = [ROOT]
        for name, skills in (('vulnerability-management', ('vulnerability-management',)),
                             ('zero-trust', ('zero-trust',)),
                             ('cmmc', ('cmmc-level-1', 'cmmc-level-2'))):
            focused = ROOT / f'plugins/ansvar-{name}'
            bases.append(focused)
            self.assertEqual({p.name for p in (focused / 'skills').iterdir()},
                             {'using-ansvar', *skills})
            for sid in ('using-ansvar', *skills):
                rel = f'skills/{sid}/SKILL.md'
                self.assertEqual((focused / rel).read_bytes(), (ROOT / rel).read_bytes())
            self.assertEqual((focused / '.mcp.json').read_bytes(), (ROOT / '.mcp.json').read_bytes())
        for base in bases:
            plugin = json.loads((base / '.claude-plugin/plugin.json').read_text())
            self.assertEqual(plugin['version'], '2.5.0')
            for field in ('icon', 'documentationUrl', 'supportUrl',
                          'privacyPolicyUrl', 'termsOfServiceUrl'):
                self.assertTrue(plugin[field])
            icon = (base / plugin['icon']).read_bytes()
            self.assertEqual(struct.unpack('>II', icon[16:24]), (512, 512))
            self.assertEqual(icon, (ROOT / '.claude-plugin/icon.png').read_bytes())

    def test_zero_trust_listing_starters_match_compiled_skill(self):
        skill = (ROOT / 'skills/zero-trust/SKILL.md').read_text()
        starters = [line for line in skill.split('## Starting a run')[1].splitlines()
                    if line.startswith('- Using Ansvar')]
        readme = (ROOT / 'plugins/ansvar-zero-trust/README.md').read_text()
        self.assertEqual([line for line in readme.splitlines() if line.startswith('- Using Ansvar')],
                         starters)


    def test_cmmc_listing_starters_match_compiled_skills(self):
        starters = []
        for sid in ('cmmc-level-1', 'cmmc-level-2'):
            skill = (ROOT / f'skills/{sid}/SKILL.md').read_text()
            starters += [line for line in skill.split('## Starting a run')[1].splitlines()
                         if line.startswith('- Using Ansvar')]
        readme = (ROOT / 'plugins/ansvar-cmmc/README.md').read_text()
        self.assertEqual([line for line in readme.splitlines() if line.startswith('- Using Ansvar')],
                         starters)
        for text in (readme, (ROOT / 'plugins/ansvar-cmmc/.claude-plugin/plugin.json').read_text()):
            self.assertIn('not a C3PAO', text)
            self.assertIn('Using Ansvar, run a CMMC Level 1', text)


if __name__ == '__main__':
    unittest.main()
