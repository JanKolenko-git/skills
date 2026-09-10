#!/usr/bin/env bash
set -uo pipefail

# Runs the eval suite the way it has to be run on this machine: the early-access flag, the
# scaffold scripts, the tool grant every Bash case needs, single-arm scoring by default —
# and, for the duration of the run, the two Docker Desktop directories that hold symlinks
# parked out of ~/.docker. The eval sandbox refuses to start a Bash-granting case while the
# Docker credential store holds a symlink anywhere inside it, and cli-plugins/ (the CLI
# plugin links into Docker.app) and bin/ (the model runner's dylib links) are where they
# live. Both are moved, never deleted, and moved back on every exit path; Docker Desktop
# recreates them on its next start regardless. While they are parked, `docker compose` and
# `docker model` do not resolve — run this when Docker is not in use.
#
# Usage: scripts/eval.sh [claude plugin eval flags]
#        scripts/eval.sh                                   # the whole suite, 3 runs each
#        scripts/eval.sh --case 'plan-change-*' --runs 1   # one skill while iterating
#        scripts/eval.sh --ablation with-without           # is the plugin earning its place?
# Later flags win, so anything passed here overrides the defaults below.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DOCKER_DIR="${HOME}/.docker"
PARK_DIR="${HOME}/.docker-parked-for-eval"
PARKED_NAMES=(cli-plugins bin)

restore() {
  local name
  for name in "${PARKED_NAMES[@]}"; do
    if [ -d "$PARK_DIR/$name" ] && [ ! -e "$DOCKER_DIR/$name" ]; then
      mv "$PARK_DIR/$name" "$DOCKER_DIR/$name" && echo "eval.sh: restored $DOCKER_DIR/$name"
    fi
  done
  rmdir "$PARK_DIR" 2>/dev/null || true
}

if [ -e "$PARK_DIR" ]; then
  echo "eval.sh: $PARK_DIR already exists — an earlier run did not restore it. Move its" >&2
  echo "         contents back under $DOCKER_DIR by hand before running again." >&2
  exit 1
fi

if [ -d "$DOCKER_DIR" ]; then
  mkdir -p "$PARK_DIR" || exit 1
  trap restore EXIT INT TERM
  for name in "${PARKED_NAMES[@]}"; do
    if [ -d "$DOCKER_DIR/$name" ]; then
      mv "$DOCKER_DIR/$name" "$PARK_DIR/$name" || exit 1
      echo "eval.sh: parked $DOCKER_DIR/$name for the run"
    fi
  done
  remaining="$(find "$DOCKER_DIR" -type l 2>/dev/null)"
  if [ -n "$remaining" ]; then
    echo "eval.sh: symlinks remain under $DOCKER_DIR, so the sandbox will still refuse:" >&2
    echo "$remaining" >&2
    exit 1
  fi
fi

cd "$REPO" || exit 1
CLAUDE_CODE_WALNUT_SPIRE=1 env -u CLAUDECODE claude plugin eval . \
  --scaffold --allow-tools Bash Write Edit --no-publish --ablation none "$@"
