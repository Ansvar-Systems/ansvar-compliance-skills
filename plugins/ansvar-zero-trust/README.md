# Ansvar Zero Trust Assessment

Assess the zero trust maturity of the systems you name against CISA ZTMM v2.0
functions, with NIST SP 800-207 as a practice reference. Receive a gap register
and a roadmap grouped by pillar, with current and target stages and the
observed, stated or unknown basis for each finding. Re-run against the previous
report to see what changed.

The skill uses twin facts when a workspace connector provides them. Otherwise
it asks interview questions and labels the answers as stated evidence. Unknowns
remain questions. ZTMM and SP 800-207 are guidance; binding requirements, such
as NIS2 Article 21 where applicable, need their own fetched authority and scope
check. Control mappings are unsupported while the ZTMM-to-800-53 crosswalk is
unavailable.

The plugin includes `using-ansvar` for one-off legal and standards questions.
Results support your own self-assessment and human review. They do not establish
legal compliance or readiness, certify compliance or maturity, or provide legal
advice.

## Install

In Claude Code:

```text
/plugin marketplace add Ansvar-Systems/ansvar-compliance-skills
/plugin install ansvar-zero-trust@ansvar-compliance-skills
/reload-plugins
```

The founder submits the separate plugin-directory listing after review.

## Try it

- Using Ansvar, assess our zero trust maturity for the systems we name.
- Using Ansvar, re-run our zero trust assessment using baseline_report_id from our previous receipt.
- Using Ansvar, identify which open zero trust gaps relate to NIS2 Article 21.

## What you need

The plugin declares the Ansvar Gateway MCP connector in `.mcp.json`
(`https://gateway.ansvar.eu/mcp`). Connect it and sign in with your Ansvar
account through OAuth. Account registration uses a business email at
[ansvar.eu](https://ansvar.eu).

Free plans include one assessment run a month, shared across Ansvar's
included workflows (Solo two); paid plans include more. The report keeps
obligations and fixes on every plan.
Live availability is decided by `get_my_capabilities` and
`list_workflow_types` before starting.

## What it sends

The plugin contains two skill files and a gateway connection. It runs no hooks
or scripts. When you ask for an assessment, your agent sends the gateway the
questions, interview answers, system scope and evidence you choose to share;
twin grounding uses the workspace facts available to the connected tools.
Workflow runs store run state. The skill presents human gates for your answer
and returns cited findings through the report receipt.

Ansvar handles that data under its [privacy policy](https://ansvar.eu/privacy)
and [terms](https://ansvar.eu/terms).

## Support

- Documentation: [ansvar.eu/docs/agent-skills](https://ansvar.eu/docs/agent-skills)
- Contact: [ansvar.eu/contact](https://ansvar.eu/contact)
- Source: [github.com/Ansvar-Systems/ansvar-compliance-skills](https://github.com/Ansvar-Systems/ansvar-compliance-skills)

Licence: CC-BY-4.0. Published by Ansvar Systems AB.
