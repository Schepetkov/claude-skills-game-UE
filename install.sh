#!/usr/bin/env bash
#
# Installs the skills in this repo into Claude Code's user-level skills directory.
#
# By default each skill is symlinked, so `git pull` in this repo updates the
# installed skills everywhere. Use --copy for independent copies.
#
# Usage:
#   ./install.sh                              # all skills, symlinked
#   ./install.sh ue-networking ue-performance # only these
#   ./install.sh --copy                       # copy instead of symlink
#   ./install.sh --target ./.claude/skills    # install into one project
#   ./install.sh --force                      # replace without asking

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$SCRIPT_DIR/skills"
TARGET="${HOME}/.claude/skills"
COPY=0
FORCE=0
SELECTED=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy)   COPY=1; shift ;;
    --force)  FORCE=1; shift ;;
    --target) TARGET="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    -*)
      echo "Unknown option: $1" >&2; exit 1 ;;
    *)
      SELECTED+=("$1"); shift ;;
  esac
done

[[ -d "$SOURCE_ROOT" ]] || { echo "No 'skills' directory next to install.sh - run this from the cloned repo." >&2; exit 1; }

AVAILABLE=()
while IFS= read -r d; do AVAILABLE+=("$(basename "$d")"); done < <(find "$SOURCE_ROOT" -mindepth 1 -maxdepth 1 -type d | sort)

if [[ ${#SELECTED[@]} -eq 0 ]]; then
  SELECTED=("${AVAILABLE[@]}")
else
  for s in "${SELECTED[@]}"; do
    found=0
    for a in "${AVAILABLE[@]}"; do [[ "$s" == "$a" ]] && found=1 && break; done
    if [[ $found -eq 0 ]]; then
      echo "Unknown skill: $s" >&2
      echo "Available: ${AVAILABLE[*]}" >&2
      exit 1
    fi
  done
fi

mkdir -p "$TARGET"

MODE=$([[ $COPY -eq 1 ]] && echo copy || echo symlink)
echo "Installing ${#SELECTED[@]} skill(s) into $TARGET ($MODE)"
echo

installed=0
skipped=0

for name in "${SELECTED[@]}"; do
  src="$SOURCE_ROOT/$name"
  dst="$TARGET/$name"

  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ $FORCE -eq 0 ]]; then
      if [[ -L "$dst" ]]; then
        detail="symlink -> $(readlink "$dst")"
      else
        detail="directory"
      fi
      printf '  ? %s already exists (%s)\n' "$name" "$detail"
      read -r -p "    Replace it? [y/N] " answer </dev/tty
      if [[ ! "$answer" =~ ^[Yy] ]]; then
        echo "    skipped"
        skipped=$((skipped + 1))
        continue
      fi
    fi
    rm -rf "$dst"
  fi

  if [[ $COPY -eq 1 ]]; then
    cp -R "$src" "$dst"
    echo "  + $name (copied)"
  else
    ln -s "$src" "$dst"
    echo "  + $name (symlink)"
  fi
  installed=$((installed + 1))
done

echo
if [[ $skipped -gt 0 ]]; then
  echo "Installed $installed skill(s), skipped $skipped."
else
  echo "Installed $installed skill(s)."
fi
echo "Run /skills in Claude Code to verify they are listed."
[[ $COPY -eq 1 ]] || echo "Linked, not copied - 'git pull' in this repo updates them in place."
