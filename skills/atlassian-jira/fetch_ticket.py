#!/usr/bin/env python3
"""Fetch a Jira ticket and print it as Markdown on stdout.

Usage:
  fetch_ticket.py <ticket-key-or-url> [--json] [--no-comments] [--comments N]

Accepts either of these as <ticket-key-or-url>:
  https://jira.example.com/browse/PROJ-1155
  PROJ-1155

Env: JIRA_URL, JIRA_PERSONAL_TOKEN (both required)
"""
import argparse
import json
import sys

from _client import browse_url, get_json, parse_key
from _markup import jira_to_markdown

FIELDS = (
    'summary,description,comment,attachment,issuelinks,labels,priority,status,'
    'assignee,reporter,components,issuetype,created,updated,parent,subtasks,'
    'resolution,fixVersions,duedate'
)


def _name(obj, key='name'):
    return (obj or {}).get(key) or None


def _person(obj):
    return (obj or {}).get('displayName') or None


def _date(value, length=10):
    return (value or '')[:length] or None


def _size(num):
    if num < 1024:
        return f'{num} B'
    if num < 1024 * 1024:
        return f'{num / 1024:.0f} KB'
    return f'{num / (1024 * 1024):.1f} MB'


def _link_lines(issuelinks):
    """Flatten issuelinks into 'relationship KEY (Status) — Title' strings."""
    lines = []
    for link in issuelinks or []:
        link_type = link.get('type') or {}
        for direction, label_key in (('outwardIssue', 'outward'), ('inwardIssue', 'inward')):
            issue = link.get(direction)
            if not issue:
                continue
            fields = issue.get('fields') or {}
            status = _name(fields.get('status')) or '?'
            label = link_type.get(label_key) or link_type.get('name') or 'relates to'
            lines.append(f'{label} **{issue.get("key")}** ({status}) — '
                         f'{fields.get("summary", "")}')
    return lines


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('target', help='ticket key or /browse/ URL')
    parser.add_argument('--json', action='store_true',
                        help='print the raw REST response instead of Markdown')
    parser.add_argument('--no-comments', action='store_true')
    parser.add_argument('--comments', type=int, default=0,
                        help='keep only the N most recent comments')
    args = parser.parse_args()

    key = parse_key(args.target)
    issue = get_json(f'/rest/api/2/issue/{key}?fields={FIELDS}')

    if args.json:
        print(json.dumps(issue, indent=2))
        return

    fields = issue.get('fields') or {}
    lines = [f'# {key} — {fields.get("summary", "(no summary)")}', '']

    meta = [
        ('Type', _name(fields.get('issuetype'))),
        ('Status', _name(fields.get('status'))),
        ('Priority', _name(fields.get('priority'))),
        ('Resolution', _name(fields.get('resolution'))),
        ('Reporter', _person(fields.get('reporter'))),
        ('Assignee', _person(fields.get('assignee')) or 'Unassigned'),
        ('Created', _date(fields.get('created'))),
        ('Updated', _date(fields.get('updated'))),
        ('Due', fields.get('duedate')),
    ]
    for label, value in meta:
        if value:
            lines.append(f'- **{label}:** {value}')

    for label, key_name in (('Labels', 'labels'), ('Components', 'components'),
                            ('Fix versions', 'fixVersions')):
        values = fields.get(key_name) or []
        if not values:
            continue
        rendered = ', '.join(v if isinstance(v, str) else v.get('name', '') for v in values)
        lines.append(f'- **{label}:** {rendered}')

    parent = fields.get('parent')
    if parent:
        parent_fields = parent.get('fields') or {}
        lines.append(f'- **Parent:** {parent.get("key")} — '
                     f'{parent_fields.get("summary", "")}')

    subtasks = fields.get('subtasks') or []
    if subtasks:
        lines.append(f'- **Subtasks ({len(subtasks)}):**')
        for sub in subtasks:
            sub_fields = sub.get('fields') or {}
            status = _name(sub_fields.get('status')) or '?'
            lines.append(f'  - {sub.get("key")} ({status}) — '
                         f'{sub_fields.get("summary", "")}')

    links = _link_lines(fields.get('issuelinks'))
    if links:
        lines.append(f'- **Linked issues ({len(links)}):**')
        lines += [f'  - {line}' for line in links]

    attachments = fields.get('attachment') or []
    if attachments:
        lines.append(f'- **Attachments ({len(attachments)}):**')
        for item in attachments:
            lines.append(f'  - {item.get("filename")} '
                         f'({item.get("mimeType", "?")}, {_size(item.get("size") or 0)}) '
                         f'— {item.get("content", "")}')

    lines.append(f'- **URL:** {browse_url(key)}')

    description = jira_to_markdown(fields.get('description'))
    lines += ['', '## Description', '']
    lines.append(description if description else '_(no description)_')

    comments = ((fields.get('comment') or {}).get('comments')) or []
    if comments and not args.no_comments:
        shown = comments[-args.comments:] if args.comments > 0 else comments
        omitted = len(comments) - len(shown)
        heading = f'## Comments ({len(comments)})'
        if omitted > 0:
            heading += f' — showing the {len(shown)} most recent'
        lines += ['', heading]
        for comment in shown:
            author = _person(comment.get('author')) or '?'
            when = _date(comment.get('created'), 16).replace('T', ' ')
            lines += ['', f'### {author} — {when}', '']
            lines.append(jira_to_markdown(comment.get('body')) or '_(empty)_')
    elif not comments:
        lines += ['', '## Comments', '', '_(none)_']

    sys.stdout.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
