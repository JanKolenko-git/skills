# Jira writes

Read when `mode` is not `read`, after the gate in `SKILL.md` → Writes. `<skill-dir>` below is
the folder holding `SKILL.md`, the one the skill printed as `${CLAUDE_SKILL_DIR}`.

## Transition status

Status is not a field you set: you run a workflow transition, and which transitions exist
depends on the ticket's current status and the project's workflow. Pass the destination
status and let the script resolve it:

```bash
python3 <skill-dir>/transition_issue.py <key-or-url> "In Review"
```

It matches the destination status first, then the transition's own name, then a unique
substring, and refuses with the available list when the match is ambiguous or absent. That
refusal is the correct outcome: the workflow does not allow that move from here, so do not
work around it by guessing an id. Close matches are fine to accept: `In Review` may resolve
to `Code Review`, `In Progress` to `In Development`. `get_transitions.py` shows the options
first.

## Add a comment

```bash
python3 <skill-dir>/add_comment.py <key-or-url> "<text>"
python3 <skill-dir>/add_comment.py <key-or-url> --stdin < body.txt
```

Wiki markup, not Markdown: `{code}...{code}`, `*bold*`, `h3.`. Everyone on the ticket sees
it, so keep an automated comment to a line or two and say what happened, not how.

## Create an issue

```bash
python3 <skill-dir>/create_issue.py --project PROJ --type Bug --summary "..." \
  --description "..." --priority Major --labels tech-debt --parent PROJ-1000
```

Projects differ in what their create screen requires. A `400` echoes Jira's own message
naming the offending field; read it instead of retrying blind.

## Edit fields

```bash
python3 <skill-dir>/edit_issue.py <key-or-url> --assignee jsmith --priority Critical
python3 <skill-dir>/edit_issue.py <key-or-url> --add-label needs-qa --remove-label triage
```

`--labels` replaces the whole list; `--add-label` / `--remove-label` leave the rest alone.
Status is not editable here; use `transition_issue.py`.

## A refused write

A failed write is not fatal to a larger flow. The workflow may not permit the move, or the
account may lack the permission: report the message and carry on. Do not abort an
orchestrating skill over a transition Jira declined, and never retry a `403` by another
route.
