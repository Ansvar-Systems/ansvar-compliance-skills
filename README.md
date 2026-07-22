# Ansvar Compliance Skills

A Claude Code plugin that bundles three published Ansvar Systems AB agent
skills for EU security and compliance work. The plugin adds no skill content
of its own — it packages the three canonical skills, unmodified, so they can
be installed as a single unit from the Claude Code plugin marketplaces.

| Skill | Invocation | What it does |
|---|---|---|
| `regulatory-threat-model` | `/ansvar-compliance-skills:regulatory-threat-model` | STRIDE and LINDDUN threat modeling, a dependency-exposure screen against live CVE / CISA-KEV / EPSS data, and a non-exhaustive screen of which EU security obligations (GDPR, NIS2, Cyber Resilience Act, AI Act) may apply. |
| `incident-reporting-navigator` | `/ansvar-compliance-skills:incident-reporting-navigator` | Screens one incident across NIS2, GDPR, DORA, and the Cyber Resilience Act, resolves which notification duties fire for each entity role, and produces a deadline table with the receiving authority per regime and member state. |
| `cra-vulnerability-obligations` | `/ansvar-compliance-skills:cra-vulnerability-obligations` | Maps a product with digital elements to Cyber Resilience Act scope, product classification, Annex I vulnerability-handling duties, and Article 14 reporting obligations. |

Every regulatory statement each skill produces is cited from officially
published text fetched live through the Ansvar Gateway MCP connector — none
of the three skills answers from model memory, and each says so explicitly
in its own SKILL.md.

## Canonical sources

This plugin vendors each skill's `SKILL.md` byte-for-byte from its own
independently published, independently licensed repository. Those repos are
the source of truth; this plugin is a wrapper:

- https://github.com/Ansvar-Systems/regulatory-threat-model-skill
- https://github.com/Ansvar-Systems/incident-reporting-navigator-skill
- https://github.com/Ansvar-Systems/cra-vulnerability-obligations-skill

`.github/workflows/anti-drift.yml` fetches each canonical `SKILL.md` from
`raw.githubusercontent.com` on every push and once a day, and fails CI red
the moment the vendored copy here diverges from the canonical repo. Run
`scripts/sync.sh` locally to re-vendor all three (or `scripts/sync.sh
--check` to diff without writing). See NOTICE for the full per-skill
attribution and license statement.

## The connector requirement

These skills do not work standalone — each one is an orchestration layer
over server-enforced tools served by the **Ansvar Gateway** MCP connector
(`https://gateway.ansvar.eu/mcp`, OAuth 2.1 via MCP Dynamic Client
Registration). This plugin declares that connector as a bundled MCP server
in `.mcp.json`, so enabling the plugin also connects Claude Code to the
gateway (subject to the normal per-server approval and OAuth prompts).

A gateway account requires sign-up at [ansvar.eu](https://ansvar.eu) with a
business email — the Free plan is B2B-gated, not self-serve for personal
email domains. Stated honestly, per skill:

- **`incident-reporting-navigator`** — everything the skill uses works on
  the Free plan.
- **`cra-vulnerability-obligations`** — everything the skill uses works on
  the Free plan.
- **`regulatory-threat-model`** — the dependency-exposure screen and the
  obligations screen work on the Free plan; the STRIDE and LINDDUN
  workflow runs require the Premium plan or above (metered monthly); the
  DPIA workflow requires the Team plan or above.

No plan tier is required to install the plugin itself — only to run the
gateway-backed workflows a given skill invokes.

## Install

### From a plugin marketplace (once approved)

Submission to the Anthropic community marketplace
(`claude-plugins-community`) is pending review at the time of writing. Once
approved:

```
/plugin marketplace add anthropics/claude-plugins-community
/plugin install ansvar-compliance-skills@claude-community
```

### Directly from this repository (available now)

This repository is itself a marketplace containing one plugin entry, so it
can be added directly without waiting on community review:

```
/plugin marketplace add Ansvar-Systems/ansvar-compliance-skills
/plugin install ansvar-compliance-skills@ansvar-compliance-skills
/reload-plugins
```

### For local development / testing

```
git clone https://github.com/Ansvar-Systems/ansvar-compliance-skills.git
claude --plugin-dir ./ansvar-compliance-skills
```

After install, run `/help` to see the three skills listed under the
`ansvar-compliance-skills` namespace, or invoke one directly, for example:

```
/ansvar-compliance-skills:incident-reporting-navigator
```

## Validation

`claude plugin validate .` passes against this repository (it validates both
`.claude-plugin/marketplace.json` and the embedded `.claude-plugin/plugin.json`
entry, since the marketplace's single plugin entry uses a local `./` source).

## License

The plugin wrapper (this manifest, the packaging, and the vendored skill
text) is licensed CC BY 4.0 — see LICENSE. Each of the three canonical skill
repos carries the same license independently; see NOTICE for the full
per-skill attribution. Regulation and guidance content the skills fetch at
runtime through the Ansvar Gateway is served from its official publishers
under their own terms, cited per row.

## About Ansvar Systems AB

Ansvar Systems AB (https://ansvar.eu) builds the Ansvar Gateway — an MCP
connector giving agents access to law, regulation, and standards corpora
across audited jurisdictions, live CVE / KEV / EPSS threat intelligence, and
server-enforced compliance workflows.
