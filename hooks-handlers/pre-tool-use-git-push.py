#!/usr/bin/env python3
"""Deterministic backstop under the review gate in git-pr-push-and-open.

That skill stops for human approval before pushing, but the stop is prose: a session
that never invokes the skill — or one whose context was compacted past it — can still
reach `git push`. Advisory controls make a violation rare; a hook makes it impossible
to reach the remote without a human answering.

Returns `ask`, never `deny`: the gate exists to be answered by a person, not to make
pushing impossible. Stdlib only, like every other script in this repo.
"""

import json
import re
import sys

# `git push`, allowing the global flags that can sit between the two words
# (`git -C /path push`, `git -c user.name=x push`) but nothing else.
GIT_PUSH = re.compile(
    r"\bgit\b(?:\s+(?:-C\s+\S+|-c\s+\S+|--git-dir=\S+|--work-tree=\S+|-\S+))*\s+push\b"
)
DRY_RUN = re.compile(r"\s(?:--dry-run|-n)\b")
FORCE = re.compile(r"\s(?:--force\b|--force-with-lease\b|-f\b)")

QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
SHELL_WRAPPER = re.compile(r"\b(?:ba|z|k)?sh\s+(?:-[a-z]*\s+)*-c\b")


def scannable(command):
    """The parts of a command where a `git push` would actually run.

    A quoted span is usually an argument to something else — `grep 'git push'`,
    `echo "git push"` — and matching inside it fires the gate on a search. The
    exception is a shell wrapper (`bash -c "git push"`), where the quoted span is
    itself a command, so there both halves are scanned.
    """
    unquoted = QUOTED.sub(" ", command)
    if SHELL_WRAPPER.search(unquoted):
        return command
    return unquoted


def ask(reason):
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.exit(0)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # Not our business; never break a session over a parse error.

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = payload.get("tool_input", {}).get("command", "")
    if not isinstance(command, str):
        sys.exit(0)

    command = scannable(command)
    if not GIT_PUSH.search(command):
        sys.exit(0)

    if DRY_RUN.search(command):
        sys.exit(0)  # Shows what would be pushed; reaches no remote.

    if FORCE.search(command):
        ask(
            "Force-push blocked by jankolenko-skills until you approve it. This "
            "rewrites history on the remote and can destroy commits other people "
            "have pulled. Confirm you mean to force-push this branch."
        )

    ask(
        "Push blocked by jankolenko-skills until you approve it. "
        "jankolenko-skills:git-pr-push-and-open owns the review gate: the diff is "
        "shown and a human says yes before anything reaches the remote. Approve "
        "here only if you have actually seen the diff."
    )


if __name__ == "__main__":
    main()
