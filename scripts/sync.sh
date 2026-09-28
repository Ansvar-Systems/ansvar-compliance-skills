#!/usr/bin/env bash
# Re-vendor (or check) the SKILL.md files this plugin copies from Ansvar's
# canonical sources. This plugin ships no skill content of its own: every
# skill body stays byte-identical to its source.
#
# Two sources, two mechanisms:
#
# 1. Four standalone skills (regulatory-threat-model, incident-reporting-
#    navigator, cra-vulnerability-obligations, iso-standards-expert). Each has
#    its own public repo; this script raw-fetches SKILL.md from its main branch.
#
# 2. The workflow skill library (the family skills in skills-manifest.json).
#    Nine family skills are compiled in Ansvar-Systems/ansvar-workflow-mcp
#    (instructions/dist/) against a pinned workflow bundle, and using-ansvar is
#    hand-published by Ansvar-Systems/ansvar-ai. Both repositories are PRIVATE,
#    so CI cannot fetch from them with this repository's token. Instead:
#      - skills-manifest.json records the wf-mcp pin (commit + sha256 of
#        instructions/dist/manifest.json, the same numbers as ansvar-ai's
#        scripts/workflow-skills.pin.json), the ansvar-ai commit for
#        using-ansvar, and the sha256 of every vendored SKILL.md.
#      - --check verifies each vendored file against those hashes (offline),
#        then compares it with the copy ansvar.eu publishes at
#        https://ansvar.eu/skills/<id>/SKILL.md (public). A mismatch there
#        means ansvar.eu moved to a newer pin: run --repin.
#      - --repin (run locally, with read access to both private repos)
#        re-reads everything from git objects, never a working tree.
#
# Usage:
#   scripts/sync.sh            # re-vendor the four standalone skills; verify the library
#   scripts/sync.sh --check    # verify all fourteen; write nothing; exit 1 on any drift
#   scripts/sync.sh --repin --wf-source <ansvar-workflow-mcp checkout> \
#                           --ai-source <ansvar-ai checkout> [--ai-ref origin/main]
#       # refresh the library from the wf-mcp commit that ansvar-ai pins at
#       # <ai-ref>, verify every hash along the chain, rewrite the vendored
#       # files and skills-manifest.json. Fetch both checkouts first.
#
# The anti-drift CI workflow (.github/workflows/anti-drift.yml) runs --check
# on every push and on a daily cron.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="sync"
WF_SOURCE=""
AI_SOURCE=""
AI_REF="origin/main"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE="check" ;;
    --repin) MODE="repin" ;;
    --wf-source) WF_SOURCE="${2:?--wf-source needs a path}"; shift ;;
    --ai-source) AI_SOURCE="${2:?--ai-source needs a path}"; shift ;;
    --ai-ref) AI_REF="${2:?--ai-ref needs a ref}"; shift ;;
    *) echo "ERROR: unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

# repo_name:local_skill_dir, one row per standalone skill.
MAPPINGS=(
  "regulatory-threat-model-skill:regulatory-threat-model"
  "incident-reporting-navigator-skill:incident-reporting-navigator"
  "cra-vulnerability-obligations-skill:cra-vulnerability-obligations"
  "iso-standards-expert-skill:iso-standards-expert"
)

STATUS=0

if [[ "${MODE}" == "repin" ]]; then
  [[ -n "${WF_SOURCE}" && -n "${AI_SOURCE}" ]] || {
    echo "ERROR: --repin needs --wf-source and --ai-source" >&2; exit 2; }
  python3 "${ROOT_DIR}/scripts/library.py" repin \
    --root "${ROOT_DIR}" --wf-source "${WF_SOURCE}" \
    --ai-source "${AI_SOURCE}" --ai-ref "${AI_REF}"
  exit $?
fi

for mapping in "${MAPPINGS[@]}"; do
  repo="${mapping%%:*}"
  dir="${mapping##*:}"
  url="https://raw.githubusercontent.com/Ansvar-Systems/${repo}/main/SKILL.md"
  target="${ROOT_DIR}/skills/${dir}/SKILL.md"
  tmp="$(mktemp)"

  echo "Fetching ${url}"
  if ! curl -fsSL "${url}" -o "${tmp}"; then
    echo "ERROR: failed to fetch ${url}" >&2
    rm -f "${tmp}"
    STATUS=1
    continue
  fi

  if [[ "${MODE}" == "check" ]]; then
    if [[ ! -f "${target}" ]]; then
      echo "DRIFT DETECTED: ${dir}/SKILL.md is missing locally"
      STATUS=1
    elif ! diff -u "${target}" "${tmp}" >/dev/null 2>&1; then
      echo "DRIFT DETECTED: skills/${dir}/SKILL.md differs from Ansvar-Systems/${repo}@main"
      diff -u "${target}" "${tmp}" || true
      STATUS=1
    else
      echo "OK: skills/${dir}/SKILL.md matches Ansvar-Systems/${repo}@main"
    fi
    rm -f "${tmp}"
  else
    mkdir -p "$(dirname "${target}")"
    mv "${tmp}" "${target}"
    echo "Vendored skills/${dir}/SKILL.md from Ansvar-Systems/${repo}@main"
  fi
done

# The library: always verified, never re-vendored outside --repin.
if ! python3 "${ROOT_DIR}/scripts/library.py" check --root "${ROOT_DIR}"; then
  STATUS=1
fi

exit "${STATUS}"
