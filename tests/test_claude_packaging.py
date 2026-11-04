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
                         '923b7332dd5f4d3ac40a1b0374dfad7670222af7')
        for entry in manifest['skills']:
            self.assertEqual(hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest(),
                             entry['sha256'])
        self.assertEqual(len(manifest['skills']), 16)
        self.assertTrue({'zero-trust', 'cmmc', 'cmmc-level-1', 'cmmc-level-2'} <=
                        {s['id'] for s in manifest['skills']})
        self.assertEqual(marketplace['metadata']['version'], '2.8.2')
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
            expected = '1.0.0' if base.name in {
                'ansvar-vulnerability-management', 'ansvar-zero-trust'} else '2.8.2'
            self.assertEqual(plugin['version'], expected)
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
        catalog = json.loads((ROOT / 'openai/catalog.json').read_text())
        item = next(p for p in catalog['plugins'] if p['id'] == 'ansvar-zero-trust')
        self.assertEqual(item['prompts'][0], starters[0].removeprefix('- '))

    def test_vulnerability_listing_starters_match_compiled_skill(self):
        skill = (ROOT / 'skills/vulnerability-management/SKILL.md').read_text()
        starters = [line for line in skill.split('## Starting a run')[1].splitlines()
                    if line.startswith('- Using Ansvar')]
        readme = (ROOT / 'plugins/ansvar-vulnerability-management/README.md').read_text()
        self.assertEqual([line for line in readme.splitlines() if line.startswith('- Using Ansvar')],
                         starters)
        catalog = json.loads((ROOT / 'openai/catalog.json').read_text())
        item = next(p for p in catalog['plugins']
                    if p['id'] == 'ansvar-vulnerability-management')
        self.assertEqual(item['prompts'][0], starters[0].removeprefix('- '))

    def test_public_readmes_describe_current_experience(self):
        zero_trust = (ROOT / 'plugins/ansvar-zero-trust/README.md').read_text()
        vulnerability = (ROOT / 'plugins/ansvar-vulnerability-management/README.md').read_text()
        cmmc = (ROOT / 'plugins/ansvar-cmmc/README.md').read_text()
        self.assertIn('three evidence batches', zero_trust)
        self.assertIn('18 decision-changing functions', zero_trust)
        self.assertIn('Deep mode covers all 40 functions', zero_trust)
        self.assertIn('three evidence\nbatches', vulnerability)
        self.assertIn('lasts one hour', zero_trust)
        self.assertIn('lasts one hour', vulnerability)
        contract = ("**Access:** I'll check what this account can run; starting the named "
                    "assessment uses one workflow allowance; I'll ask before starting.")
        self.assertIn(contract, zero_trust)
        self.assertIn(contract, vulnerability)
        self.assertIn('Release version: 1.0.0.', zero_trust)
        self.assertIn('Release version: 1.0.0.', vulnerability)
        self.assertIn('gateway-observed infrastructure failure', zero_trust)
        self.assertIn('never self-asserts', zero_trust)
        for readme in (zero_trust, vulnerability, cmmc):
            self.assertNotIn('founder submits', readme.lower())


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
