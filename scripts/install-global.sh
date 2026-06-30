#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

uv tool install --force .
uv tool update-shell || true

TOOL_BIN="${UV_TOOL_BIN_DIR:-$HOME/.local/bin}"

cat <<'MSG'

Installed the global `ms` command.
MSG

if command -v ms >/dev/null 2>&1; then
  cat <<'MSG'

`ms` is available now:

  ms --help

MSG
else
  cat <<MSG

Your current shell does not have $TOOL_BIN on PATH yet.

For this terminal session, run:

  export PATH="$TOOL_BIN:\$PATH"

Then test:

  ms --help

New terminals should pick this up after restarting your shell.

MSG
fi
