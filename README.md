# Ansvar Compliance Skills

A Claude Code plugin that bundles fourteen published Ansvar Systems AB agent
skills for EU security and compliance work. The plugin adds no skill content
of its own: it packages the canonical skills, unmodified, so they install as
one unit.

The fourteen come in two groups:

- **Four standalone skills**, each published in its own public repository.
- **The workflow skill library**: nine family skills compiled by Ansvar from
  its workflow definitions, plus `using-ansvar`, the routing skill for
  one-off legal and standards questions. These are the skills
  [ansvar.eu/docs/agent-skills](https://ansvar.eu/docs/agent-skills)
  publishes.

Every claim a skill produces is cited from officially published or licensed
text fetched live through the Ansvar Gateway MCP connector. None of the
skills answers from model memory, and each says so in its own SKILL.md.

Each skill is invoked by its directory name under the plugin's namespace,
for example `/ansvar-compliance-skills:threat-model`. The family skills
carry `name: ansvar-<family>` in their frontmatter. Claude Code 2.1.283
lists them by directory name, and in a test on that version both
`/ansvar-compliance-skills:tabletop` and
`/ansvar-compliance-skills:ansvar-tabletop` loaded the skill. The Claude
Code documentation says the frontmatter `name` sets the command, so other
versions may show the `ansvar-` form.

### Standalone skills

| Skill | Invocation | What it does |
|---|---|---|
| `regulatory-threat-model` | `/ansvar-compliance-skills:regulatory-threat-model` | STRIDE and LINDDUN threat modeling, a dependency-exposure screen against live CVE / CISA-KEV / EPSS data, and a non-exhaustive screen of which EU security obligations (GDPR, NIS2, Cyber Resilience Act, AI Act) may apply. |
| `incident-reporting-navigator` | `/ansvar-compliance-skills:incident-reporting-navigator` | Screens one incident across NIS2, GDPR, DORA, and the Cyber Resilience Act, resolves which notification duties fire for each entity role, and produces a deadline table with the receiving authority per regime and member state. |
| `cra-vulnerability-obligations` | `/ansvar-compliance-skills:cra-vulnerability-obligations` | Maps a product with digital elements to Cyber Resilience Act scope, product classification, Annex I vulnerability-handling duties, and Article 14 reporting obligations. |
| `iso-standards-expert` | `/ansvar-compliance-skills:iso-standards-expert` | Cited clause-level support on SS-EN ISO/IEC 27001:2023, 27002:2022, 27005:2024, 42001:2026 and SS-ISO/SAE 21434:2021 — licensed standard text served under Ansvar's SIS reproduction licence, quoted verbatim with attribution; only selected parts of a standard, never the complete standard. |

### Workflow skill library

| Skill | Invocation | What it does |
|---|---|---|
| `using-ansvar` | `/ansvar-compliance-skills:using-ansvar` | Routes any question about what a law, regulation or security standard says through the gateway, searches with an explicit scope, and answers only from fetched rows with a per-claim citation. |
| `gap-analysis` | `/ansvar-compliance-skills:gap-analysis` | Assesses an organisation against a regulatory framework control by control, with article-level citations and a coverage score (NIS2 and its Dutch and Polish transpositions, DORA, CRA, AI Act, MDR, IVDR, UNECE R155, the Machinery Regulation, drone rules). |
| `threat-model` | `/ansvar-compliance-skills:threat-model` | STRIDE security threat models and LINDDUN privacy threat models over a described system, with scored threats and mapped controls; AI/ML, OT/ICS and drone variants. |
| `dpia` | `/ansvar-compliance-skills:dpia` | GDPR Article 35 data protection impact assessments and EU AI Act Article 27 fundamental rights impact assessments, with German and Swedish variants. |
| `tara` | `/ansvar-compliance-skills:tara` | Risk assessments with likelihood and consequence bands, scored against declared thresholds and closed with treatments, including automotive (ISO/SAE 21434), rail, robotics, OT and UAS TARA. |
| `tender-review` | `/ansvar-compliance-skills:tender-review` | Bidder-side completeness review of a public tender and buyer-side lawfulness audit of the tender itself, each requirement cited to its legal basis; Dutch and Swedish variants. |
| `vulnerability-decisions` | `/ansvar-compliance-skills:vulnerability-decisions` | Contextual scoring of an already-scanned finding set with KEV and EPSS, a costed control-investment plan, deferral records for what stays open, and a merged CycloneDX VEX. |
| `tabletop` | `/ansvar-compliance-skills:tabletop` | A crisis simulation run turn by turn against a scripted adversary, scored from the decisions the team made, with an after-action report. |
| `document-review` | `/ansvar-compliance-skills:document-review` | Reviews an uploaded document against a regulatory baseline, with every finding anchored to a paragraph-level citation and a content hash. |
| `drone-operations` | `/ansvar-compliance-skills:drone-operations` | A SORA determination chain for a specific-category UAS operation: ground and air risk, SAIL, the operational safety objectives with robustness levels, and containment. |

Each family skill ends with openings you can paste to your agent. One from
each:

- `gap-analysis`: "Using Ansvar, run a NIS2 gap analysis for our managed hosting business in the Netherlands."
- `threat-model`: "Using Ansvar, run a STRIDE threat model on the OT network at our bottling plant."
- `dpia`: "Using Ansvar, run a DPIA for the employee monitoring we are rolling out in Germany."
- `tara`: "Using Ansvar, run a TARA for the telematics unit in our commercial vehicle platform."
- `tender-review`: "Using Ansvar, review this Swedish public tender and tell me what our bid is missing."
- `vulnerability-decisions`: "Using Ansvar, score this SBOM scan against how our product is actually deployed."
- `tabletop`: "Using Ansvar, run a ransomware tabletop exercise for our incident response team."
- `document-review`: "Using Ansvar, review our data processing agreement against GDPR Articles 28 and 32."
- `drone-operations`: "Using Ansvar, run a SORA for BVLOS powerline inspection over sparsely populated terrain."

Start with "Using Ansvar". Without the name, the agent may answer from its
own memory and never call the connector.

### `regulatory-threat-model` or `threat-model`?

Both run the gateway's STRIDE and LINDDUN workflows, and both are composed
over the same shared fragments of Ansvar's workflow instruction library (the
run loop and the delivery rules). They differ in scope:

- **`regulatory-threat-model`** is a whole-application security review. Around
  the STRIDE run (and the LINDDUN run when personal data flows) it adds a
  dependency-exposure screen against CVE, CISA KEV and EPSS data and a screen
  of which EU security obligations may apply, and it has a free lane that
  still produces a cited deliverable when no workflow run is available. It
  states the plan rules itself. Use it to review an application before it
  ships or goes in front of a customer.
- **`threat-model`** drives the threat-model workflows directly: STRIDE,
  LINDDUN, and the AI/ML, OT/ICS and drone variants. It does no dependency
  or obligations screen, and it reads what the caller may start from the
  live workflow catalogue instead of stating plan rules. Use it when you
  want a threat model of a described system, in particular one of the
  variants.

When both could fit, name the one you want by its command.

Plan notes: the four standalone skills and `using-ansvar` state their own
plan rules (summarised under [The connector
requirement](#the-connector-requirement)). The nine family skills do not:
at run time each calls `list_workflow_types`, and a workflow the caller's
plan cannot start is marked `available_to_caller: false` with a tier
caveat. The ISO skill's licensed clause lane needs the paid, per-standard
[ISO Standards add-on](https://ansvar.eu/standards) (purchasable on any
plan, including Free); without it that skill runs in its labelled SCF
cross-reference lane.

## Canonical sources

This plugin vendors every `SKILL.md` byte for byte. The sources are the
truth; this plugin is a wrapper.

**Standalone skills**, one public repository each:

- https://github.com/Ansvar-Systems/regulatory-threat-model-skill
- https://github.com/Ansvar-Systems/incident-reporting-navigator-skill
- https://github.com/Ansvar-Systems/cra-vulnerability-obligations-skill
- https://github.com/Ansvar-Systems/iso-standards-expert-skill

`scripts/sync.sh` fetches each `SKILL.md` from `raw.githubusercontent.com`
and re-vendors it; `scripts/sync.sh --check` diffs without writing.

**Workflow skill library.** The nine family skills are compiled in
Ansvar's workflow repository against a pinned workflow bundle, with a
manifest that carries a sha256 per file; `using-ansvar` is maintained in
Ansvar's website repository. Both repositories are private. ansvar.eu
publishes the exact bytes at `https://ansvar.eu/skills/<id>/SKILL.md`
from a pin (source commit plus manifest sha256), and this plugin follows
the same pin. `skills-manifest.json` records it: the source commit, the
manifest sha256, the website commit the pin was read from, and the sha256
of each vendored file. Nothing in this repository lists the families by
hand; `--repin` takes them from the upstream manifest.

- `scripts/sync.sh --check` verifies each library file against
  `skills-manifest.json` without network access, fails on any skill
  directory that belongs to neither group, and then compares each file
  with the public copy on ansvar.eu. A mismatch there means the website
  moved to a newer pin.
- `scripts/sync.sh --repin --wf-source <workflow repo checkout> --ai-source
  <website repo checkout>` refreshes the library. It needs read access to
  both private repositories, reads bytes from git objects only, checks
  every hash along the chain, and rewrites the files and
  `skills-manifest.json`.

`.github/workflows/anti-drift.yml` runs `scripts/sync.sh --check` on every
push and once a day. A failure turns CI red and opens (or comments on) the
issue `anti-drift: vendored skills diverge from canonical`. See NOTICE for
the per-skill attribution and license statement.

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

- **`using-ansvar`** — works on every plan, including Free; on Free each
  search carries exactly one jurisdiction or one framework.
- **The nine family skills** — admission per workflow comes from the live
  catalogue, as described under Plan notes above.

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

After install, run `/help` to see the fourteen skills listed under the
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
text) is licensed CC BY 4.0 — see LICENSE. Each skill carries the same license
in its own SKILL.md; see NOTICE for the full
per-skill attribution. Regulation and guidance content the skills fetch at
runtime through the Ansvar Gateway is served from its official publishers
under their own terms, cited per row.

## About Ansvar Systems AB

Ansvar Systems AB (https://ansvar.eu) builds the Ansvar Gateway — an MCP
connector giving agents access to law, regulation, and standards corpora
across audited jurisdictions, live CVE / KEV / EPSS threat intelligence, and
server-enforced compliance workflows.
