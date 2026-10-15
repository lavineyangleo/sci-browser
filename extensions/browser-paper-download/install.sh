#!/usr/bin/env bash
# Install browser-paper-download into one or more AI coding agent harnesses.
#
# Usage:
#   ./install.sh <target> [target...]   # zcode claude codex opencode goose amp agents all
#   ./install.sh --dest <dir>           # custom skills directory
#   ./install.sh --list                 # show known targets and their directories
#
# "all" installs into every harness whose config directory already exists
# (add --force to create the missing ones too). Re-running updates in place.
# Payload copied: SKILL.md, references/, scripts/  (.git, __pycache__, OS junk excluded).
set -euo pipefail

SKILL_NAME="browser-paper-download"
HERE="$(cd "$(dirname "$0")" && pwd)"
FORCE=0
DEST=""

usage() {
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
}

each_target() {  # one known target per line
  echo "zcode claude codex opencode goose amp agents" | tr ' ' '\n'
}

dest_for() {
  case "$1" in
    zcode)    echo "$HOME/.zcode/skills" ;;
    claude)   echo "$HOME/.claude/skills" ;;
    codex)    echo "${CODEX_HOME:-$HOME/.codex}/skills" ;;
    opencode) echo "$HOME/.config/opencode/skills" ;;
    goose)    echo "$HOME/.config/goose/skills" ;;
    amp)      echo "$HOME/.config/amp/skills" ;;
    agents)   echo "$HOME/.agents/skills" ;;  # portable multi-agent convention
    *)        return 1 ;;
  esac
}

harness_home() {  # parent directory whose existence implies the harness is installed
  case "$1" in
    zcode)    echo "$HOME/.zcode" ;;
    claude)   echo "$HOME/.claude" ;;
    codex)    echo "${CODEX_HOME:-$HOME/.codex}" ;;
    opencode) echo "$HOME/.config/opencode" ;;
    goose)    echo "$HOME/.config/goose" ;;
    amp)      echo "$HOME/.config/amp" ;;
    agents)   echo "$HOME/.agents" ;;
  esac
}

install_into() {
  local dest="$1"
  local skill_dir="$dest/$SKILL_NAME"
  mkdir -p "$dest"
  rm -rf "$skill_dir"
  mkdir -p "$skill_dir"
  cp -R "$HERE/SKILL.md" "$HERE/references" "$HERE/scripts" "$skill_dir/"
  find "$skill_dir" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
  find "$skill_dir" -name .DS_Store -delete 2>/dev/null || true
  chmod +x "$skill_dir"/scripts/*.py 2>/dev/null || true
  echo "installed -> $skill_dir"
}

install_target() {  # one named target, honoring FORCE
  local t="$1" home
  home="$(harness_home "$t")"
  if [ "$FORCE" -eq 0 ] && [ ! -d "$home" ]; then
    echo "skip $t ($home not found; harness not installed? use --force)"
    return 0
  fi
  install_into "$(dest_for "$t")"
}

# ---- parse args ----
[ $# -eq 0 ] && usage
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --list)
      for t in $(each_target); do printf "%-9s %s\n" "$t" "$(dest_for "$t")"; done
      exit 0 ;;
    --dest)  [ $# -ge 2 ] || usage; DEST="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    -h|--help) usage ;;
    --*)     echo "unknown option: $1" >&2; exit 1 ;;
    *)       ARGS+=("$1"); shift ;;
  esac
done

if [ -n "$DEST" ]; then
  if [ "${#ARGS[@]}" -gt 0 ]; then echo "--dest cannot be combined with targets" >&2; exit 1; fi
  install_into "$DEST"
  exit 0
fi
[ "${#ARGS[@]}" -gt 0 ] || usage

# ---- install ----
for target in "${ARGS[@]}"; do
  if [ "$target" != "all" ] && ! dest_for "$target" >/dev/null 2>&1; then
    echo "unknown target: $target (try --list)" >&2; exit 1
  fi
done
for target in "${ARGS[@]}"; do
  if [ "$target" = "all" ]; then
    for t in $(each_target); do install_target "$t"; done
  else
    install_target "$target"
  fi
done
