# Ansvar CMMC Self-Assessment

Run a CMMC Level 1 or Level 2 self-assessment for a US defence contract. Your
agent records the scope, assets, boundary and External Service Providers under
32 CFR 170.19, fetches every NIST SP 800-171 requirement and assessment
objective it assesses from the `nist-cui` corpus, and submits one finding per
objective with the evidence you name. The Ansvar engine computes the result
under 32 CFR 170.24: Level 1 is met or not met across 15 requirements, with no
score; Level 2 is scored out of 110, with the POA&M the rule allows and the
blockers to Conditional status. The report lists the SPRS inputs and carries
the affirmation for your Affirming Official.

The plugin holds two skills, `cmmc-level-1` and `cmmc-level-2`, plus
`using-ansvar` for one-off legal and standards questions. A conditional
Level 2 result can be closed out later with a POA&M closeout run.

This is a self-assessment aid. It is not a C3PAO assessment or certification,
and it is not legal advice. A solicitation that names Level 2 (C3PAO) needs a
certified third-party assessment; the skill says so and stops. Your Affirming
Official reviews the findings and gives the affirmation.

Phase 2 of the CMMC rollout begins on 10 November 2026 (32 CFR 170.3(e)).

## Install

In Claude Code:

```text
/plugin marketplace add Ansvar-Systems/ansvar-compliance-skills
/plugin install ansvar-cmmc@ansvar-compliance-skills
/reload-plugins
```

The founder submits the separate plugin-directory listing after review.

## Try it

- Using Ansvar, run a CMMC Level 1 self-assessment for our company; we handle Federal Contract Information only.
- Using Ansvar, walk me through our annual CMMC Level 1 self-assessment and affirmation.
- Using Ansvar, run our CMMC Level 1 self-assessment and list the evidence records each requirement still needs.
- Using Ansvar, run a CMMC Level 2 self-assessment for the systems that handle our CUI.
- Using Ansvar, run our CMMC Level 2 self-assessment and show me the score, status and POA&M the engine returns.
- Using Ansvar, close out the POA&M from our conditional CMMC Level 2 assessment, workflow <workflow_id>.

## What you need

The plugin declares the Ansvar Gateway MCP connector in `.mcp.json`
(`https://gateway.ansvar.eu/mcp`). Connect it and sign in with your Ansvar
account through OAuth. Account registration uses a business email at
[ansvar.eu](https://ansvar.eu).

Level 1 (`cmmc_l1_self`) is included in the Free and Solo plans as one of the
types the monthly included workflow run can be spent on, and runs on Premium,
Team and Company. Level 2 (`cmmc_l2_self`) and the base type
(`cmmc_self_assessment`) run on Team and Company. Level 2 needs a current
System Security Plan. Live availability is decided by `get_my_capabilities`
and `list_workflow_types` before starting.

## What it sends

The plugin contains three skill files and a gateway connection. It runs no
hooks or scripts. When you ask for an assessment, your agent sends the gateway
the scope, findings and evidence references you choose to share: `customer://`
locators, or uploaded documents on plans that allow uploads. Workflow runs
store run state. The skill presents each human gate, including scope approval
and the affirmation review, for your answer and returns the result through the
report receipt.

Ansvar handles that data under its [privacy policy](https://ansvar.eu/privacy)
and [terms](https://ansvar.eu/terms).

## Support

- Documentation: [ansvar.eu/docs/agent-skills](https://ansvar.eu/docs/agent-skills)
- Contact: [ansvar.eu/contact](https://ansvar.eu/contact)
- Source: [github.com/Ansvar-Systems/ansvar-compliance-skills](https://github.com/Ansvar-Systems/ansvar-compliance-skills)

Licence: CC-BY-4.0. Published by Ansvar Systems AB.
