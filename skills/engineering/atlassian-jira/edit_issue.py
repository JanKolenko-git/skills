#!/usr/bin/env python3
"""Edit fields on an existing Jira issue.

Usage:
  edit_issue.py PROJ-1234 --summary "Better title"
  edit_issue.py PROJ-1234 --assignee jsmith --priority Critical
  edit_issue.py PROJ-1234 --add-label needs-qa --remove-label triage
  edit_issue.py PROJ-1234 --labels a,b,c          # replaces the whole list

Status is NOT a field — use transition_issue.py for that. Jira rejects a direct
write to `status`, and the workflow decides what is reachable anyway.

`--labels` replaces every label on the issue; `--add-label` / `--remove-label`
leave the others alone. Prefer the latter unless you mean to clear the list.

Env: JIRA_URL, JIRA_PERSONAL_TOKEN (both required)
"""
import argparse

from _client import base_url, parse_key, send_json


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('key', help='ticket key or browse URL')
    parser.add_argument('--summary', help='replace the title')
    parser.add_argument('--description', help='replace the body (Jira wiki markup)')
    parser.add_argument('--priority', help='priority name, e.g. Major')
    parser.add_argument('--assignee', help='username; pass "none" to unassign')
    parser.add_argument('--labels', help='comma-separated — REPLACES all labels')
    parser.add_argument('--add-label', action='append', default=[],
                        dest='add_labels', help='add one label (repeatable)')
    parser.add_argument('--remove-label', action='append', default=[],
                        dest='remove_labels', help='remove one label (repeatable)')
    args = parser.parse_args()

    fields = {}
    update = {}

    if args.summary:
        fields['summary'] = args.summary
    if args.description:
        fields['description'] = args.description
    if args.priority:
        fields['priority'] = {'name': args.priority}
    if args.assignee:
        fields['assignee'] = (None if args.assignee.lower() == 'none'
                              else {'name': args.assignee})
    if args.labels:
        fields['labels'] = [l.strip() for l in args.labels.split(',') if l.strip()]

    label_ops = ([{'add': l} for l in args.add_labels]
                 + [{'remove': l} for l in args.remove_labels])
    if label_ops:
        if 'labels' in fields:
            parser.error('--labels replaces the whole list, so combining it with '
                         '--add-label/--remove-label is contradictory. Pick one.')
        update['labels'] = label_ops

    if not fields and not update:
        parser.error('nothing to change — pass at least one field option')

    payload = {}
    if fields:
        payload['fields'] = fields
    if update:
        payload['update'] = update

    key = parse_key(args.key)
    send_json(f'/rest/api/2/issue/{key}', payload, method='PUT')

    changed = sorted(list(fields) + list(update))
    print(f'Updated {key}: {", ".join(changed)} — {base_url()}/browse/{key}')


if __name__ == '__main__':
    main()
