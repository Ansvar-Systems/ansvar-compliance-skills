#!/usr/bin/env bash
# Re-vendor (or check) the SKILL.md files copied from Ansvar's canonical,
# independently published skill repos. This plugin ships no skill content of
# its own — every skill body must stay byte-identical to its canonical repo.
#
# Usage:
#   scripts/sync.sh            # fetch each canonical SKILL.md and overwrite the vendored copy
#   scripts/sync.sh --check    # fetch and diff only; write nothing; exit 1 on any drift
#
# The anti-drift CI workflow (.github/workflows/anti-drift.yml) runs this in
# --check mode on every push and on a daily cron. A non-empty diff is red CI.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK_ONLY=0
if [[ "${1:-}" == "--check" ]]; then
  CHECK_ONLY=1
fi

# repo_name:local_skill_dir — one row per vendored skill. Keep this list in
# sync with skills/*/SKILL.md; it is the single source both this script and
# the CI workflow read.
MAPPINGS=(
  "regulatory-threat-model-skill:regulatory-threat-model"
  "incident-reporting-navigator-skill:incident-reporting-navigator"
  "cra-vulnerability-obligations-skill:cra-vulnerability-obligations"
)

STATUS=0

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

  if [[ "${CHECK_ONLY}" -eq 1 ]]; then
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

exit "${STATUS}"
