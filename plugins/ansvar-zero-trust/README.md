# Ansvar Zero Trust Assessment

Assess the zero trust maturity of the systems you name against the 40
functions of the CISA Zero Trust Maturity Model v2.0, with NIST SP 800-207 as a
practice reference. Before the first question your agent tells you what the
assessment covers, what it costs on your plan, how many replies it takes and what to
have ready. You choose a target stage for each pillar; your agent never picks
one for you. Re-run against the previous report to see what changed.

The skill uses twin facts when a workspace connector provides them. Otherwise
it asks interview questions and labels the answers as stated evidence. Unknowns
remain questions. ZTMM and SP 800-207 are guidance; binding requirements, such
as NIS2 Article 21 where applicable, need their own fetched authority and scope
check. Your agent records each regulation it evaluated and whether it applies
to you; a regulation it fetched is not an obligation by itself. The report
can include NIST SP 800-53 candidates from the served SP 1800-35 crosswalk
on Team and Company, marked related-to for review rather than coverage.

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

## Try it

- Using Ansvar, assess our zero trust maturity for the systems we name.
- Using Ansvar, re-run our zero trust assessment with baseline_report_id <report id from our previous receipt> and show what changed.
- Using Ansvar, identify which open zero trust gaps relate to NIS2 Article 21.

## What to have ready

- The systems in scope.
- How people and services sign in: identity provider, MFA, service credentials.
- How devices are managed.
- Network segmentation and remote access.
- How applications are deployed and tested.
- Data classification and encryption.
- Logging, and who reviews it.

Any of these can be "unknown"; it becomes an open question in the report, not a
guess.

## Effort

Plan for 15 to 30 minutes with records at hand in default mode. You answer
three evidence batches covering 18 decision-changing functions, then review
the proposed stages in one table. Deep mode covers all 40 functions in six
batches. You can pause after any batch. The replay measurement for this release
is recorded separately from these package instructions.

## What you get

- A register with current and target stages for each assessed function; default
  mode labels the other functions for a later deep-mode run.
- A priority (P1 first) and effort in days, weeks or a quarter for each gap.
- The regulations evaluated, and whether each applies to you.
- Open questions for everything recorded as unknown.
- A roadmap ordered by priority, with first actions.
- A report id (`baseline_report_id`) that lets the next run show what changed.
- An HTML report link that lasts one hour; download it within that hour.

## What you need

The plugin declares the Ansvar Gateway MCP connector in `.mcp.json`
(`https://gateway.ansvar.eu/mcp`). Connect it and sign in with your Ansvar
account through OAuth. Account registration uses a business email at
[ansvar.eu](https://ansvar.eu).

Free and Solo include one and two workflow runs a month, shared across the
included workflows; Premium and above run the assessment from the monthly
allowance. Starting a run spends one. A deliberate cancellation is not handed
back; after bounded retries exhaust a gateway-observed infrastructure failure,
the gateway can restore the run under its bounded monthly safeguard. Your agent
never self-asserts that reason, and names the workflow and asks before it starts.
The report keeps obligations and fixes on every plan.
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
