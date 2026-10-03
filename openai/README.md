# Focused ChatGPT and Codex plugins

This directory builds Ansvar Citation Check, Ansvar AI Compliance and Ansvar
Privacy Review as separate portable Agent Plugins packages. Each bundles its
own focused skill and the existing authenticated Ansvar Gateway connection.

These are release candidates. Local package checks and read-only gateway probes
have run; no candidate has been installed through ChatGPT, submitted or published.
The first Privacy Review release covers controller-processor DPAs.

## Build and verify

From the repository root, with Python 3:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/openai_plugins.py check
python3 scripts/openai_plugins.py build
python3 scripts/openai_plugins.py verify-dist
```

The builder writes one ZIP per catalog entry and checksums to `openai/dist/`.
That directory is generated and ignored by git. `check` validates source inputs
and reconstructs packages in memory; `verify-dist` also compares the existing
ZIP bytes, archive roster and checksums with the current sources. Run
`verify-dist` immediately before uploading. Zip contents use an explicit
allowlist and contain no repository internals, credentials or review results.

Author focused instructions in `src/`, listing text and review cases in
`catalog.json`, and account/evidence boundaries in `shared/`. The build copies
these to each package. Update the catalog version when preparing a new release.

The workflow execution and report-delivery fragments in `vendor/` and the
brand icon in `assets/` are generated imports. Do not edit them. Their source
commits and hashes live in `upstream-lock.json`. The importer follows the
workflow release pinned by the public website, verifies its manifest, and reads
immutable git objects. To check or update after fetching the source checkouts:

```bash
python3 scripts/openai_plugins.py check-upstream --wf-source /path/to/ansvar-workflow-mcp --ai-source /path/to/ansvar-ai
python3 scripts/openai_plugins.py repin --wf-source /path/to/ansvar-workflow-mcp --ai-source /path/to/ansvar-ai
```

Review the changed inputs, bump the package version and rebuild after a repin.
CI validates the current pinned inputs and packaging invariants; it does not
claim that private upstream repositories have not moved. Run `check-upstream`
before each release. The existing Claude-package anti-drift checks stay separate.

## Submission packet

Each manifest includes listing copy, brand assets, legal/support URLs, example
prompts, one MCP URL, and five positive plus three negative review cases.
The endpoint is `https://gateway.ansvar.eu/mcp`; configure OAuth through the
portal. Do not add tokens or authentication headers to a ZIP.

Use a dedicated reviewer account with synthetic data. Its credentials belong in
the secure portal form, never in this repository or package metadata. Before
submission:

1. Install each candidate in ChatGPT and connect the intended reviewer account.
   Confirm the delivered tools match that account. All packages use the same
   gateway; the skill narrows task behavior but is not a server-side tool filter.
   The portal must review the full exposed MCP surface.
2. Run all review cases from that ZIP. Record observed results, account tier,
   client surface and package SHA-256. The expected results in `catalog.json`
   are authored test specifications, not execution evidence.
3. Complete an AI assessment and a DPA review on synthetic inputs with the
   required human gates. Verify report delivery, document references and quota
   behavior. Also check an account without document access and one without the
   selected workflow allowance.
4. Record a walkthrough showing the plugin behavior and test cases. Enter its
   reviewer-accessible video URL and the dedicated account details in the portal.
5. Upload the verified ZIP, scan the MCP, resolve findings and submit for review.
   After approval, publish the approved version.

Public metadata intentionally omits a demo recording URL until a real recording
exists. Account verification, reviewer credentials, installed-client tests and
the recording remain release tasks. The current read-only probes are recorded in
[read-only-probes.json](review/read-only-probes.json).

Each listing has a distinct task and output. Confirm acceptance of the shared
MCP connection in the portal; local package validation does not prove directory
approval or server registration reuse. Do not create alternate gateway routes
or replace the existing Ansvar Gateway listing to work around a portal error.

## Maintenance and evidence

The package tests cover byte-reproducible archives, source-hash tampering,
missing references, archive drift, listing limits and unsafe source symlinks.
The existing anti-drift workflow runs these checks and records a failed check
through its issue path. No additional hosted job is introduced.

On 2026-10-03 the candidates also passed the published Agent Plugins 1.0.0
plugin and MCP JSON schemas and the skill-creator frontmatter validator.
Those schema checks do not validate every OpenAI extension or runtime behavior.

The live citation probe distinguished a resolved reference, a matching quote
with an omitted-tail warning, and an altered quote. The AI scoping probe
identified the high-risk-provider workflow; the skill explicitly checks fit
before starting it. Probes used the existing company connection and do not prove
access on lower tiers.

Official references consulted on 2026-10-03:

- [Package format](https://developers.openai.com/plugins/build/plugins)
- [Submission requirements](https://developers.openai.com/plugins/deploy/submission)
- [Plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines)
- [Portable manifest schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json)
- [Portable MCP schema](https://agent-plugins.org/schemas/1.0.0/mcp.schema.json)
