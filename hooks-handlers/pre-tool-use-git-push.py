#!/usr/bin/env python3
"""Deterministic backstop under the review gate in git-pr-push-and-open.

That skill stops for human approval before pushing, but the stop is prose: a session
that never invokes the skill — or one whose context was compacted past it — can still
reach `git push`. Advisory controls make a violation rare; a hook makes it impossible
to reach the remote without a human answering.

Scoped to the pushes that are actually expensive to undo — the default branch, force,
branch deletion, and bulk pushes. A feature branch goes through silently: prompting on
every push trains you to approve without reading, which costs more than it protects.

Returns `ask`, never `deny`: the gate exists to be answered by a person, not to make
pushing impossible. Stdlib only, like every other script in this repo.
"""

import json
import os
import re
import shlex
import subprocess
import sys

# `git push`, allowing the global flags that can sit between the two words
# (`git -C /path push`, `git -c user.name=x push`) but nothing else.
GIT_PUSH = re.compile(
    r"\bgit\b(?:\s+(?:-C\s+\S+|-c\s+\S+|--git-dir=\S+|--work-tree=\S+|-\S+))*\s+push\b"
)
DRY_RUN = re.compile(r"\s(?:--dry-run|-n)\b")
FORCE = re.compile(r"\s(?:--force\b|--force-with-lease\b|-f\b)")
DELETE = re.compile(r"\s(?:--delete\b|-d\b)")
BULK = re.compile(r"\s(?:--all\b|--mirror\b|--tags\b)")

QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
SHELL_WRAPPER = re.compile(r"\b(?:ba|z|k)?sh\s+(?:-[a-z]*\s+)*-c\b")

# Flags that consume the next token, so it is not the remote or a refspec.
VALUE_FLAGS = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}

FALLBACK_PROTECTED = {"main", "master"}


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


def git(cwd, *args):
    try:
        out = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def protected_branches(cwd):
    """The repo's default branch, plus the usual names as a floor."""
    names = set(FALLBACK_PROTECTED)
    head = git(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if head:
        names.add(head.split("/")[-1])
    return names


def push_arguments(command, match_end):
    """Tokens after `push`, stopping at the next command in the line."""
    tail = re.split(r"[;&|\n]", command[match_end:])[0]
    try:
        return shlex.split(tail)
    except ValueError:
        # Unbalanced quotes — a shell wrapper's closing quote lands in the tail
        # (`bash -c "git push origin main"`). Strip them, or the branch name keeps
        # a trailing quote and silently fails to match a protected name.
        return [token.strip("\"'") for token in tail.split()]


def targets(args, cwd):
    """Branch names this push would write to, or None when it cannot be determined.

    None means ask. Guessing wrong here means a silent push to the default branch,
    so an unparseable command is treated as the dangerous case, not the safe one.
    """
    positional = []
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
            continue
        if arg in VALUE_FLAGS:
            skip_next = True
            continue
        if arg.startswith("-"):
            continue
        positional.append(arg)

    refspecs = positional[1:]  # positional[0] is the remote
    if not refspecs:
        current = git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
        return [current] if current else None

    names = []
    for spec in refspecs:
        dest = spec.strip("\"'").split(":")[-1]
        dest = re.sub(r"^refs/heads/", "", dest)
        if dest in ("HEAD", ""):
            current = git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
            if not current:
                return None
            dest = current
        names.append(dest)
    return names


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

    raw = payload.get("tool_input", {}).get("command", "")
    if not isinstance(raw, str):
        sys.exit(0)

    command = scannable(raw)
    match = GIT_PUSH.search(command)
    if not match:
        sys.exit(0)

    if DRY_RUN.search(command):
        sys.exit(0)  # Shows what would be pushed; reaches no remote.

    if FORCE.search(command):
        ask(
            "Force-push held by jankolenko-skills until you approve it. This rewrites "
            "history on the remote and can destroy commits other people have pulled. "
            "Confirm you mean to force-push."
        )

    if DELETE.search(command):
        ask(
            "Branch deletion on the remote, held by jankolenko-skills until you approve "
            "it. Confirm you mean to delete this branch for everyone."
        )

    if BULK.search(command):
        ask(
            "Bulk push (--all / --mirror / --tags) held by jankolenko-skills until you "
            "approve it. This writes more refs than the branch you are on, and --mirror "
            "can delete remote branches that do not exist locally."
        )

    cwd = payload.get("cwd") or os.getcwd()
    branches = targets(push_arguments(command, match.end()), cwd)

    if branches is None:
        ask(
            "jankolenko-skills could not work out which branch this push targets, so it "
            "is asking rather than assuming. Check the refspec before approving."
        )

    protected = protected_branches(cwd)
    hit = [b for b in branches if b in protected]
    if hit:
        ask(
            f"Push to '{hit[0]}' held by jankolenko-skills until you approve it. "
            "jankolenko-skills:git-pr-push-and-open owns the review gate — normally work "
            "reaches the default branch through a reviewed PR, not a direct push."
        )

    sys.exit(0)  # A feature branch. The skill's own gate covers this one.


if __name__ == "__main__":
    main()
