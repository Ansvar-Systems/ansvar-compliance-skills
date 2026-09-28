# Ansvar Compliance Skills

A Claude Code plugin that bundles four published Ansvar Systems AB agent
skills for EU security and compliance work. The plugin adds no skill content
of its own — it packages the four canonical skills, unmodified, so they can
be installed as a single unit from the Claude Code plugin marketplaces.

| Skill | Invocation | What it does |
|---|---|---|
| `regulatory-threat-model` | `/ansvar-compliance-skills:regulatory-threat-model` | STRIDE and LINDDUN threat modeling, a dependency-exposure screen against live CVE / CISA-KEV / EPSS data, and a non-exhaustive screen of which EU security obligations (GDPR, NIS2, Cyber Resilience Act, AI Act) may apply. |
| `incident-reporting-navigator` | `/ansvar-compliance-skills:incident-reporting-navigator` | Screens one incident across NIS2, GDPR, DORA, and the Cyber Resilience Act, resolves which notification duties fire for each entity role, and produces a deadline table with the receiving authority per regime and member state. |
| `cra-vulnerability-obligations` | `/ansvar-compliance-skills:cra-vulnerability-obligations` | Maps a product with digital elements to Cyber Resilience Act scope, product classification, Annex I vulnerability-handling duties, and Article 14 reporting obligations. |
| `iso-standards-expert` | `/ansvar-compliance-skills:iso-standards-expert` | Cited clause-level support on SS-EN ISO/IEC 27001:2023, 27002:2022, 27005:2024, 42001:2026 and SS-ISO/SAE 21434:2021 — licensed standard text served under Ansvar's SIS reproduction licence, quoted verbatim with attribution; only selected parts of a standard, never the complete standard. |

Every claim each skill produces is cited from officially published or
licensed text fetched live through the Ansvar Gateway MCP connector — none
of the four skills answers from model memory, and each says so explicitly
in its own SKILL.md.

Plan note: the threat-model, incident-reporting and CRA skills have free
lanes on a free gateway account, with paid features varying by skill and
plan. The ISO skill's licensed clause lane needs the paid, per-standard [ISO Standards
add-on](https://ansvar.eu/standards) (purchasable on any plan, including
Free); without it that skill still runs in its labelled SCF
cross-reference lane.

## Canonical sources

This plugin vendors each skill's `SKILL.md` byte-for-byte from its own
independently published, independently licensed repository. Those repos are
the source of truth; this plugin is a wrapper:

- https://github.com/Ansvar-Systems/regulatory-threat-model-skill
- https://github.com/Ansvar-Systems/incident-reporting-navigator-skill
- https://github.com/Ansvar-Systems/cra-vulnerability-obligations-skill
- https://github.com/Ansvar-Systems/iso-standards-expert-skill

`.github/workflows/anti-drift.yml` fetches each canonical `SKILL.md` from
`raw.githubusercontent.com` on every push and once a day, and fails CI red
the moment the vendored copy here diverges from the canonical repo. Run
`scripts/sync.sh` locally to re-vendor all four (or `scripts/sync.sh
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
email domains. Per skill:

- **`incident-reporting-navigator`** — everything the skill uses works on
  the Free plan.
- **`cra-vulnerability-obligations`** — everything the skill uses works on
  the Free plan.
- **`regulatory-threat-model`** — the free lane (intake, the
  dependency-exposure screen, the obligations screen and the written
  deliverable) works on the Free plan. The STRIDE workflow run is
  included on every plan within a monthly run allowance (1 run on Free,
  2 on Solo, 5 on Premium, 20 per seat pooled on Team, uncapped on
  Company); on Free and Solo the allowance is a hard stop. The LINDDUN
  privacy run requires Premium or above. The base DPIA workflow is
  included from Free within the same allowance; its jurisdictional
  variants require Premium. Report formats also vary by plan: see the
  skill's own Plan notes.

No plan tier is required to install the plugin itself — only to run the
gateway-backed workflows a given skill invokes.

## Install

### From Anthropic's plugin directory

The plugin is listed in Anthropic's plugin directory, the catalog you
browse on claude.ai and in Cowork. One listing covers claude.ai, Cowork
and Claude Code:

1. On claude.ai or in Cowork, open the plugin directory, find **Ansvar
   Compliance Skills**, and add it to your account.
2. In Claude Code, sign in with the same claude.ai account (Claude Code
   v2.1.273 or later). Claude Code syncs the plugin in the background
   when it starts and loads it as `ansvar-compliance-skills@synced`. If
   the session prints `Plugins changed. Run /reload-plugins to
   activate.`, run `/reload-plugins`.

A directory plugin has no `/plugin install` command: it reaches Claude
Code through account sync, not through a marketplace you add. See
[Plugins synced from
claude.ai](https://code.claude.com/docs/en/plugins/loading#synced-plugins)
and [Anthropic's
marketplaces](https://code.claude.com/docs/en/plugins/anthropic-marketplaces).
To turn it off in Claude Code only, run `claude plugin disable
ansvar-compliance-skills@synced`.

### Directly from this repository

This repository is itself a marketplace containing one plugin entry, so
you can add it without a claude.ai account:

```
/plugin marketplace add Ansvar-Systems/ansvar-compliance-skills
/plugin install ansvar-compliance-skills@ansvar-compliance-skills
/reload-plugins
```

Use one route, not both: when the synced copy and a marketplace copy
share the name, Claude Code loads the marketplace copy and reports the
synced one as not loaded.

### For local development / testing

```
git clone https://github.com/Ansvar-Systems/ansvar-compliance-skills.git
claude --plugin-dir ./ansvar-compliance-skills
```

After install, run `/help` to see the four skills listed under the
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
text) is licensed CC BY 4.0 — see LICENSE. Each of the four canonical skill
repos carries the same license independently; see NOTICE for the full
per-skill attribution. Regulation and guidance content the skills fetch at
runtime through the Ansvar Gateway is served from its official publishers
under their own terms, cited per row.

## About Ansvar Systems AB

Ansvar Systems AB (https://ansvar.eu) builds the Ansvar Gateway — an MCP
connector giving agents access to law, regulation, and standards corpora
across audited jurisdictions, live CVE / KEV / EPSS threat intelligence, and
server-enforced compliance workflows.
