#!/usr/bin/env python3
"""Create a Jira issue.

Usage:
  create_issue.py --project PROJ --type Bug --summary "Cart total wrong on VAT"
  create_issue.py --project PROJ --type Task --summary "..." --description "..." \
      --priority Major --labels tech-debt,frontend --parent PROJ-1000

Prints the new key and its browse URL.

Projects differ in which fields their create screen requires — some demand a
component, a fix version, or a custom field. A 400 here echoes Jira's own message
naming the offending field; read it rather than retrying blind.

Env: JIRA_URL, JIRA_PERSONAL_TOKEN (both required)
"""
import argparse

from _client import base_url, parse_key, send_json


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('--project', required=True, help='project key, e.g. PROJ')
    parser.add_argument('--type', required=True, dest='issue_type',
                        help='issue type name, e.g. Bug, Story, Task')
    parser.add_argument('--summary', required=True, help='the title')
    parser.add_argument('--description', help='body, in Jira wiki markup')
    parser.add_argument('--priority', help='priority name, e.g. Major')
    parser.add_argument('--labels', help='comma-separated labels')
    parser.add_argument('--components', help='comma-separated component names')
    parser.add_argument('--assignee', help='username to assign to')
    parser.add_argument('--parent', help='parent key, when creating a subtask')
    args = parser.parse_args()

    fields = {
        'project': {'key': args.project.upper()},
        'issuetype': {'name': args.issue_type},
        'summary': args.summary,
    }

    if args.description:
        fields['description'] = args.description
    if args.priority:
        fields['priority'] = {'name': args.priority}
    if args.labels:
        fields['labels'] = [l.strip() for l in args.labels.split(',') if l.strip()]
    if args.components:
        fields['components'] = [{'name': c.strip()}
                                for c in args.components.split(',') if c.strip()]
    if args.assignee:
        fields['assignee'] = {'name': args.assignee}
    if args.parent:
        fields['parent'] = {'key': parse_key(args.parent)}

    result = send_json('/rest/api/2/issue', {'fields': fields})

    key = (result or {}).get('key')
    if not key:
        print('Issue created, but Jira returned no key in the response.')
        return
    print(f'Created {key} — {base_url()}/browse/{key}')


if __name__ == '__main__':
    main()
