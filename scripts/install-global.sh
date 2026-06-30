#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

uv tool install --force .

TOOL_BIN="${UV_TOOL_BIN_DIR:-$HOME/.local/bin}"
PATH_LINE="export PATH=\"$TOOL_BIN:\$PATH\""
MARKER="# model-shelf ms command"

ensure_path_file() {
  local file="$1"
  mkdir -p "$(dirname "$file")"
  touch "$file"
  if grep -Fq "$TOOL_BIN" "$file"; then
    return
  fi
  {
    printf '\n%s\n' "$MARKER"
    printf '%s\n' "$PATH_LINE"
  } >> "$file"
  printf 'Updated %s\n' "$file"
}

case "${SHELL:-}" in
  */zsh)
    ensure_path_file "$HOME/.zshrc"
    ensure_path_file "$HOME/.zprofile"
    ensure_path_file "$HOME/.zshenv"
    ;;
  */bash)
    ensure_path_file "$HOME/.bashrc"
    ensure_path_file "$HOME/.bash_profile"
    ;;
  *)
    ensure_path_file "$HOME/.zshrc"
    ensure_path_file "$HOME/.bashrc"
    ;;
esac

cat <<'MSG'

Installed the global `ms` command.
MSG

if PATH="$TOOL_BIN:$PATH" command -v ms >/dev/null 2>&1; then
  cat <<'MSG'

`ms` is installed.

For this terminal session, run:

  export PATH="$TOOL_BIN:$PATH"

Then test:

  ms --help

New terminals should pick this up automatically.

MSG
else
  cat <<MSG

The executable was installed to:

  $TOOL_BIN

For this terminal session, run:

  export PATH="$TOOL_BIN:\$PATH"

Then test:

  ms --help

New terminals should pick this up after restarting your shell.

MSG
fi
