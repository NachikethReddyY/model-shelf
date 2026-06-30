#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

uv tool install --force .
uv tool update-shell

cat <<'MSG'

Installed the global `ms` command.

Restart your shell, then run:

  ms --help

MSG
