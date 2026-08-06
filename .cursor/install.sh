#!/usr/bin/env bash
# Idempotent Cloud Agent setup for structlog-config.
# Installs the mise-managed toolchain (Python, uv, just, direnv) pinned in
# mise.toml and syncs all Python dependency groups + extras (matching CI's
# full test run).
set -euo pipefail

export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"

# Install mise (tool-version manager) if it is not already available.
if ! command -v mise >/dev/null 2>&1; then
  curl -fsSL https://mise.run | sh
fi

# Make the toolchain available in future (interactive and non-interactive)
# shells. Adding the shims directory to PATH covers non-interactive shells,
# while `mise activate` handles interactive ones.
BASHRC="$HOME/.bashrc"
MARKER="# >>> structlog-config mise activation >>>"
if ! grep -qF "$MARKER" "$BASHRC" 2>/dev/null; then
  {
    echo "$MARKER"
    echo 'export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"'
    echo 'eval "$(mise activate bash)" 2>/dev/null || true'
    echo "# <<< structlog-config mise activation <<<"
  } >>"$BASHRC"
fi

# Install the pinned toolchain from mise.toml / mise.lock.
mise trust
mise install

# Activate the toolchain for the rest of this script.
eval "$(mise activate bash --shims)"

# Provide a local .env for direnv-based workflows (Justfile `setup`).
[ -f .env ] || cp .env-example .env

# Install all dependency groups and extras, matching the full CI test job.
uv sync --all-groups --all-extras
