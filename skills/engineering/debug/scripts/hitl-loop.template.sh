#!/usr/bin/env bash
# A reproduction loop that needs a human: the agent runs this script, the person follows
# the prompts in their terminal, and every observation comes back as KEY=VALUE lines the
# agent can read. Copy it, replace the steps between the markers, run it.
#
# Usage: bash hitl-loop.template.sh
#
#   step "<what to do>"              shows the instruction and waits for Enter
#   capture NAME "<what to report>"  shows the question and stores the answer in NAME
#
# Anything captured is echoed back to the terminal the agent reads, so capture
# observations only; a sign-in or a password prompt stays a `step`.

set -euo pipefail

step() {
  printf '\n>>> %s\n' "$1"
  read -r -p '    [Enter when done] ' _
}

capture() {
  local name="$1" question="$2" reply
  printf '\n>>> %s\n' "$question"
  read -r -p '    > ' reply
  printf -v "$name" '%s' "$reply"
}

# --- steps: replace from here ----------------------------------------------

step "Open http://localhost:3000 and sign in."
capture THREW "Press the button under test. Did it throw? (y/n)"
capture MESSAGE "Paste the error message, or 'none':"

# --- to here -----------------------------------------------------------------

printf '\n--- Captured ---\n'
printf 'THREW=%s\n' "$THREW"
printf 'MESSAGE=%s\n' "$MESSAGE"
