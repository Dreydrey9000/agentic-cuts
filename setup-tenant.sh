#!/usr/bin/env bash
# Agentic Cuts — tenant scaffolder.
#
# Spins up a new tenant repo on GitHub under the active gh account, wires the
# core engine in as a git submodule, and drops a starter brand-kit.yaml that
# the new tenant fills in.
#
# Usage:
#   ./setup-tenant.sh
#     (interactive — prompts for slug, name, primary color)
#
#   AC_TENANT_SLUG=newbrand AC_TENANT_NAME="New Brand" AC_PRIMARY_HEX="#ff2d3a" \
#       ./setup-tenant.sh
#     (non-interactive — uses env vars)
#
# Requires: gh, git, python3.

set -euo pipefail

CORE_REPO="${AC_CORE_REPO:-https://github.com/Dreydrey9000/agentic-cuts.git}"

prompt_or_env() {
    local var_name="$1"
    local prompt_text="$2"
    local default_value="${3:-}"
    local current_value
    current_value="$(eval echo \$$var_name)"
    if [[ -n "$current_value" ]]; then
        echo "$current_value"
        return
    fi
    if [[ -n "$default_value" ]]; then
        read -r -p "$prompt_text [$default_value]: " input
        echo "${input:-$default_value}"
    else
        read -r -p "$prompt_text: " input
        echo "$input"
    fi
}

require_bin() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "ERR: $1 not found on PATH. Install it first." >&2
        exit 1
    }
}

require_bin gh
require_bin git
require_bin python3

echo "=== Agentic Cuts — Tenant Setup ==="

TENANT_SLUG="$(prompt_or_env AC_TENANT_SLUG "Tenant slug (lowercase, no spaces, e.g. 'drey')")"
TENANT_NAME="$(prompt_or_env AC_TENANT_NAME "Display name (e.g. 'Drey')")"
TENANT_DESC="$(prompt_or_env AC_TENANT_DESC "One-line description" "${TENANT_NAME}'s whitelisted Agentic Cuts instance.")"
PRIMARY_HEX="$(prompt_or_env AC_PRIMARY_HEX "Primary brand hex" "#ffd200")"
ACCENT_HEX="$(prompt_or_env AC_ACCENT_HEX "Accent brand hex" "#ff2d3a")"
TYPO_FAMILY="$(prompt_or_env AC_TYPO_FAMILY "Primary font family" "Inter")"
VOICE_ID="$(prompt_or_env AC_VOICE_ID "Default narration voice" "kokoro/af_bella")"
DEFAULT_PRESET="$(prompt_or_env AC_DEFAULT_PRESET "Default caption preset" "podcast-clean")"
VISIBILITY="$(prompt_or_env AC_VISIBILITY "Repo visibility (public|private)" "private")"

if [[ ! "$TENANT_SLUG" =~ ^[a-z0-9_-]+$ ]]; then
    echo "ERR: tenant slug must be lowercase alphanumeric (with - or _ allowed): got '$TENANT_SLUG'" >&2
    exit 1
fi

REPO_NAME="agentic-cuts-${TENANT_SLUG}"
WORK_DIR="$HOME/My Apps/${REPO_NAME}"

if [[ -d "$WORK_DIR" ]]; then
    echo "ERR: $WORK_DIR already exists. Pick a different slug or remove the existing directory." >&2
    exit 1
fi

echo
echo "=== Plan ==="
echo "  Repo:        $REPO_NAME ($VISIBILITY)"
echo "  Local dir:   $WORK_DIR"
echo "  Brand:       $TENANT_NAME"
echo "  Primary:     $PRIMARY_HEX  Accent: $ACCENT_HEX"
echo "  Voice:       $VOICE_ID"
echo "  Captions:    $DEFAULT_PRESET"
echo
read -r -p "Proceed? [y/N] " confirm
if [[ "${confirm:-N}" != "y" && "${confirm:-N}" != "Y" ]]; then
    echo "Aborted."
    exit 0
fi

echo "[1/5] Creating GitHub repo..."
gh repo create "$REPO_NAME" --"$VISIBILITY" \
    --description "$TENANT_DESC" \
    --license apache-2.0 \
    --add-readme \
    --gitignore Python \
    >/dev/null
GH_LOGIN="$(gh api user --jq .login)"

echo "[2/5] Cloning..."
git clone "https://github.com/${GH_LOGIN}/${REPO_NAME}.git" "$WORK_DIR" >/dev/null 2>&1

echo "[3/5] Wiring core as submodule..."
cd "$WORK_DIR"
git submodule add "$CORE_REPO" core >/dev/null 2>&1

echo "[4/5] Generating brand-kit.yaml..."
python3 - <<PYEOF
from pathlib import Path
import yaml

bk = {
    "tenant_id": "$TENANT_SLUG",
    "display_name": "$TENANT_NAME",
    "description": "$TENANT_DESC",
    "palette": [
        {"name": "primary", "hex": "$PRIMARY_HEX"},
        {"name": "accent",  "hex": "$ACCENT_HEX"},
        {"name": "ink",     "hex": "#0c0c0c"},
        {"name": "paper",   "hex": "#f5f1e8"},
    ],
    "primary_typography": {"family": "$TYPO_FAMILY", "weight": 800, "italic": False},
    "voice": {"primary_voice": "$VOICE_ID", "speaking_rate": 1.0, "pitch": 0.0},
    "captions": {"default_preset": "$DEFAULT_PRESET", "accent_color_override": "$PRIMARY_HEX"},
    "default_pipelines": ["clip-factory", "talking-head", "podcast-repurpose"],
    "no_emojis": True,
    "hashtags": [],
}
Path("brand-kit.yaml").write_text(yaml.safe_dump(bk, sort_keys=False, allow_unicode=True))
PYEOF

cat > CHANGELOG.md <<EOF
# Changelog — Agentic Cuts ($TENANT_NAME Tenant)

## [$(date +%Y-%m-%d)]

### Added
- Tenant scaffolded via setup-tenant.sh.
- Core engine wired as git submodule at \`./core\`.
- \`brand-kit.yaml\` populated from setup defaults.
EOF

git add brand-kit.yaml CHANGELOG.md .gitmodules core
git commit -m "chore: scaffold tenant via setup-tenant.sh

Tenant: $TENANT_NAME ($TENANT_SLUG)
Primary: $PRIMARY_HEX  Accent: $ACCENT_HEX
Default voice: $VOICE_ID
Default caption preset: $DEFAULT_PRESET
" >/dev/null

echo "[5/5] Pushing to GitHub on bootstrap branch..."
git checkout -b bootstrap >/dev/null 2>&1
git push -u origin bootstrap >/dev/null 2>&1

echo
echo "=== Done ==="
echo "  Local:   $WORK_DIR"
echo "  Remote:  https://github.com/${GH_LOGIN}/${REPO_NAME}"
echo "  Branch:  bootstrap (open a PR to land on main)"
echo
echo "Next: edit brand-kit.yaml to taste, then 'cd \"$WORK_DIR\" && code .'"
