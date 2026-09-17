#!/usr/bin/env python3
"""Measure what the skill layer costs in context, and fail above budget.

Four surfaces are paid for: every skill's description sits in the listing of every session;
the session-start hook is injected into every session; ENGINEERING.md is read before any
code change; a skill's body is loaded when it runs and stays for the rest of the session.
This script prints all four, estimates tokens (chars / 4), and exits 1 when any surface
exceeds its budget — the same way check-portable.py fails on a ticket key.

BUDGETS are the enforced caps. TARGETS are where the plan says each number ends up; they
are printed for reference and tightened into BUDGETS one batch at a time.

Usage: scripts/measure.py            # table + breaches; exit 1 on any breach
       scripts/measure.py --json     # the same numbers as JSON, for recording a baseline
"""
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS_PER_TOKEN = 4  # a rough, deliberately simple estimate; consistent across runs is what matters

BUDGETS = {
    "description_chars": 350,          # per model-invoked skill: description + when_to_use
    "description_total_chars": 6000,  # sum over the model-invoked skills in skills/; 18 listed at ~330 each
    "body_words": 1100,                # per skill, prose words (fenced code excluded)
    "body_lines": 500,                 # Anthropic's ceiling for a SKILL.md body
    "hook_chars": 950,                # the additionalContext the session-start hook injects
    "engineering_words": 2200,         # ENGINEERING.md, prose words
}

TARGETS = {
    "description_chars": 350,
    "description_total_chars": 5500,
    "body_lines": 500,
    "hook_chars": 800,
    "engineering_words": 2200,
    "body_words": {
        "git-pr-address-review": 800,
        "implement": 700,
        "record-engineering-rule": 600,
        "prepare-local-environment": 650,
        "atlassian-jira": 650,
        "find-session-improvements": 500,
        "atlassian-confluence": 550,
        "improve-skill": 450,
        "plan": 650,
        "record-learnings": 450,
        "explain": 450,
        "git-pr-push-and-open": 450,
        "draft-reply": 400,
        "check": 700,
        "find-skill-gaps": 400,
        "find-repository": 350,
        "git-commit": 350,
        "test": 400,
        "git-create-branch": 300,
        "debug": 650,
        "architect": 450,
        "document": 450,
    },
}
DEFAULT_TARGET_WORDS = 500

FENCE = re.compile(r"```.*?```", re.S)


def parse_frontmatter(text):
    """Return (fields, body). Handles single-line values and `>`/`|` block scalars."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text
    fields = {}
    i = 1
    while i < end:
        match = re.match(r"^([A-Za-z_-]+):\s*(.*)$", lines[i])
        if not match:
            i += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if value in (">", "|", ">-", "|-"):
            block = []
            i += 1
            while i < end and (lines[i].startswith(" ") or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            fields[key] = " ".join(part for part in block if part)
            continue
        fields[key] = value.strip("\"'")
        i += 1
    return fields, "\n".join(lines[end + 1:])


def measure_skill(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    fields, body = parse_frontmatter(text)
    prose = FENCE.sub("", body)
    return {
        "name": fields.get("name", os.path.basename(os.path.dirname(path))),
        "listed": fields.get("disable-model-invocation", "false").lower() != "true",
        "description_chars": len(fields.get("description", "")) + len(fields.get("when_to_use", "")),
        "body_words": len(prose.split()),
        "body_lines": body.count("\n"),
        "body_tokens": len(body) // CHARS_PER_TOKEN,
    }


def find_skills(root, depth):
    """SKILL.md files at exactly `depth` directories under root, sorted."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        level = 0 if rel == "." else rel.count(os.sep) + 1
        if level > depth:
            dirnames[:] = []
            continue
        if level == depth and "SKILL.md" in filenames:
            found.append(os.path.join(dirpath, "SKILL.md"))
    return sorted(found)


def measure_hook():
    """Run the session-start hook the way Claude Code does and measure what it injects."""
    script = os.path.join(REPO, "hooks-handlers", "session-start.sh")
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=REPO, CLAUDE_PROJECT_DIR=REPO)
    result = subprocess.run(["bash", script], cwd=REPO, env=env, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"session-start.sh exited {result.returncode}: {result.stderr.strip()}")
    payload = json.loads(result.stdout)
    return len(payload["hookSpecificOutput"]["additionalContext"])


def measure_engineering():
    with open(os.path.join(REPO, "ENGINEERING.md"), encoding="utf-8") as fh:
        text = fh.read()
    return len(FENCE.sub("", text).split()), len(text) // CHARS_PER_TOKEN


def main():
    as_json = "--json" in sys.argv[1:]
    general = [measure_skill(p) for p in find_skills(os.path.join(REPO, "skills"), 2)]
    projects_root = os.path.join(REPO, "projects")
    project = [measure_skill(p) for p in find_skills(projects_root, 3)] if os.path.isdir(projects_root) else []
    hook_chars = measure_hook()
    engineering_words, engineering_tokens = measure_engineering()
    description_total = sum(s["description_chars"] for s in general if s["listed"])

    breaches = []
    for skill in general:
        target_words = TARGETS["body_words"].get(skill["name"], DEFAULT_TARGET_WORDS)
        skill["target_words"] = target_words
        if skill["listed"] and skill["description_chars"] > BUDGETS["description_chars"]:
            breaches.append(f"{skill['name']}: description {skill['description_chars']} chars > {BUDGETS['description_chars']}")
        if skill["body_words"] > BUDGETS["body_words"]:
            breaches.append(f"{skill['name']}: body {skill['body_words']} words > {BUDGETS['body_words']}")
        if skill["body_lines"] > BUDGETS["body_lines"]:
            breaches.append(f"{skill['name']}: body {skill['body_lines']} lines > {BUDGETS['body_lines']}")
    if description_total > BUDGETS["description_total_chars"]:
        breaches.append(f"descriptions total {description_total} chars > {BUDGETS['description_total_chars']}")
    if hook_chars > BUDGETS["hook_chars"]:
        breaches.append(f"hook {hook_chars} chars > {BUDGETS['hook_chars']}")
    if engineering_words > BUDGETS["engineering_words"]:
        breaches.append(f"ENGINEERING.md {engineering_words} words > {BUDGETS['engineering_words']}")

    report = {
        "skills": general,
        "project_skills": project,
        "description_total_chars": description_total,
        "hook_chars": hook_chars,
        "engineering_words": engineering_words,
        "engineering_tokens": engineering_tokens,
        "budgets": BUDGETS,
        "breaches": breaches,
    }
    if as_json:
        print(json.dumps(report, indent=1))
        return 1 if breaches else 0

    header = f"{'skill':28s} {'listed':>6s} {'desc':>5s} {'words':>6s} {'target':>6s} {'lines':>5s} {'~tok':>5s}"
    print(header)
    print("-" * len(header))
    for skill in general:
        print(f"{skill['name']:28s} {'yes' if skill['listed'] else 'no':>6s} {skill['description_chars']:5d} "
              f"{skill['body_words']:6d} {skill['target_words']:6d} {skill['body_lines']:5d} {skill['body_tokens']:5d}")
    if project:
        print(f"\nprojects/ (reported, not enforced):")
        for skill in project:
            print(f"{skill['name']:28s} {'yes' if skill['listed'] else 'no':>6s} {skill['description_chars']:5d} "
                  f"{skill['body_words']:6d} {'-':>6s} {skill['body_lines']:5d} {skill['body_tokens']:5d}")
    listed = [s for s in general if s["listed"]]
    print(f"\ndescriptions: {description_total} chars over {len(listed)} listed skills "
          f"(~{description_total // CHARS_PER_TOKEN} tokens every session; cap {BUDGETS['description_total_chars']}, "
          f"target {TARGETS['description_total_chars']})")
    print(f"hook:         {hook_chars} chars (~{hook_chars // CHARS_PER_TOKEN} tokens every session; "
          f"cap {BUDGETS['hook_chars']}, target {TARGETS['hook_chars']})")
    print(f"ENGINEERING:  {engineering_words} words (~{engineering_tokens} tokens per code change; "
          f"cap {BUDGETS['engineering_words']}, target {TARGETS['engineering_words']})")
    total_body = sum(s["body_words"] for s in general)
    total_target = sum(s["target_words"] for s in general)
    print(f"bodies:       {total_body} words across {len(general)} skills (target {total_target})")

    if breaches:
        print("\nOVER BUDGET:")
        for line in breaches:
            print(f"  {line}")
        return 1
    print("\nbudgets: within limits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
