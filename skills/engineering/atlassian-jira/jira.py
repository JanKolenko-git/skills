#!/usr/bin/env python3
"""Read and write Jira Server / Data Center tickets over REST v2.

  jira.py fetch <key-or-url> [--comments N | --no-comments] [--json]
  jira.py search "<jql-or-text>" [--project PROJ] [--limit 20]
  jira.py transitions <key-or-url>
  jira.py transition <key-or-url> <status-or-id>
  jira.py comment <key-or-url> "<text>" | --stdin
  jira.py create --project PROJ --type Bug --summary "..." [--description ...] [...]
  jira.py edit <key-or-url> [--summary ...] [--assignee ...] [--add-label ...] [...]
  jira.py download <content-url> <dest-path>

<key-or-url> is a key like PROJ-1155 or any Jira URL containing one. `--help` on a
subcommand lists its options. There is no delete subcommand.

Env: JIRA_URL, JIRA_PERSONAL_TOKEN (both required)
"""
import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

from _client import EXIT_SETUP, base_url, die, fetch, get_json, send_json

FIELDS = (
    'summary,description,comment,attachment,issuelinks,labels,priority,status,'
    'assignee,reporter,components,issuetype,created,updated,parent,subtasks,'
    'resolution,fixVersions,duedate'
)


# -- targets ---------------------------------------------------------------------

def parse_key(arg):
    """Extract a ticket key from a browse URL, an issue URL, or a bare key."""
    arg = arg.strip()
    if re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*-\d+', arg):
        return arg.upper()

    match = re.search(r'/browse/([A-Za-z][A-Za-z0-9_]*-\d+)', arg)
    if match:
        return match.group(1).upper()

    parsed = urllib.parse.urlparse(arg if '://' in arg else f'https://{arg}')
    query = urllib.parse.parse_qs(parsed.query)
    for name in ('selectedIssue', 'issueKey', 'key'):
        if name in query:
            return query[name][0].upper()

    match = re.search(r'([A-Za-z][A-Za-z0-9_]*-\d+)', arg)
    if match:
        return match.group(1).upper()

    die(f'could not find a ticket key in {arg!r}. Pass a key like PROJ-1234 or a '
        f'/browse/ URL.')


def browse_url(key):
    return f'{base_url()}/browse/{key}'


# -- formatting ------------------------------------------------------------------

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


def _text(value):
    """A description or comment body as Jira stored it: wiki markup, which reads as
    it is. Only the line endings are normalised."""
    return (value or '').replace('\r\n', '\n').strip()


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


# -- fetch -----------------------------------------------------------------------

def cmd_fetch(args):
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

    description = _text(fields.get('description'))
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
            lines.append(_text(comment.get('body')) or '_(empty)_')
    elif not comments:
        lines += ['', '## Comments', '', '_(none)_']

    sys.stdout.write('\n'.join(lines) + '\n')


# -- search ----------------------------------------------------------------------

def looks_like_jql(text):
    return bool(re.search(r'(=|~|\bORDER\s+BY\b|\bAND\b|\bOR\b|\bIN\b\s*\()',
                          text, re.I))


def cmd_search(args):
    if looks_like_jql(args.query):
        jql = args.query
    else:
        needle = args.query.replace('\\', '\\\\').replace('"', '\\"')
        jql = f'text ~ "{needle}"'

    if args.project and 'project' not in jql.lower():
        jql = f'project = "{args.project}" AND ({jql})'
    if 'order by' not in jql.lower():
        jql += ' ORDER BY updated DESC'

    url = (f'/rest/api/2/search?jql={urllib.parse.quote(jql)}'
           f'&maxResults={args.limit}&fields=summary,status')

    issues = get_json(url).get('issues', [])
    if not issues:
        print(f'No issues matched. (JQL: {jql})')
        return

    for issue in issues:
        fields = issue.get('fields') or {}
        status = ((fields.get('status') or {}).get('name')) or '?'
        key = issue.get('key')
        print(f'{key}  [{status}]  {fields.get("summary", "")}  —  {browse_url(key)}')


# -- transitions -----------------------------------------------------------------

def _transitions(key):
    """What the workflow offers from the ticket's current status. It depends on the
    status and the project's workflow, so a status reachable yesterday may not be
    reachable today: read it, never assume an id."""
    data = get_json(f'/rest/api/2/issue/{key}/transitions')
    return data.get('transitions', [])


def _describe(transitions):
    return '\n'.join(
        f"  {t['id']}\t{t['name']}\t->\t{t.get('to', {}).get('name', '?')}"
        for t in transitions
    ) or '  (none — the workflow offers no transitions from the current status)'


def _resolve(transitions, wanted):
    """Find the transition to run. Destination status first, then the transition's
    own name, then a unique substring match on the destination. A name is checked
    against what the workflow offers, so it cannot invent a transition; a guessed
    id can. No match prints the available list and exits non-zero rather than
    moving the ticket somewhere merely adjacent."""
    if wanted.isdigit():
        for t in transitions:
            if t['id'] == wanted:
                return t
        die(f'no transition with id {wanted}. Available:\n{_describe(transitions)}',
            EXIT_SETUP)

    target = wanted.strip().lower()

    for t in transitions:
        if t.get('to', {}).get('name', '').lower() == target:
            return t

    for t in transitions:
        if t['name'].lower() == target:
            return t

    partial = [t for t in transitions
               if target in t.get('to', {}).get('name', '').lower()]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        die(f'{wanted!r} matches more than one destination:\n{_describe(partial)}\n'
            f'Re-run with the exact status name or the transition id.', EXIT_SETUP)

    die(f'no transition leads to {wanted!r} from the current status. Available:\n'
        f'{_describe(transitions)}', EXIT_SETUP)


def cmd_transitions(args):
    key = parse_key(args.target)
    transitions = _transitions(key)
    if not transitions:
        print(f'{key}: no transitions available from its current status.')
        return
    for t in transitions:
        dest = t.get('to', {}).get('name', '?')
        print(f"{t['id']}\t{t['name']}\t->\t{dest}")


def cmd_transition(args):
    key = parse_key(args.target)
    chosen = _resolve(_transitions(key), args.transition)

    send_json(f'/rest/api/2/issue/{key}/transitions',
              {'transition': {'id': chosen['id']}}, method='POST')

    dest = chosen.get('to', {}).get('name', '?')
    print(f'{key} -> {dest}  (via "{chosen["name"]}", id {chosen["id"]})')


# -- comment, create, edit ---------------------------------------------------------

def cmd_comment(args):
    body = sys.stdin.read() if args.stdin else args.body
    if not body or not body.strip():
        args.parser.error('empty comment body — pass text as an argument or use --stdin')

    key = parse_key(args.target)
    result = send_json(f'/rest/api/2/issue/{key}/comment', {'body': body}, method='POST')

    comment_id = (result or {}).get('id', '?')
    print(f'Commented on {key} (comment {comment_id}) — '
          f'{browse_url(key)}?focusedCommentId={comment_id}')


def cmd_create(args):
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

    result = send_json('/rest/api/2/issue', {'fields': fields}, method='POST')

    key = (result or {}).get('key')
    if not key:
        print('Issue created, but Jira returned no key in the response.')
        return
    print(f'Created {key} — {browse_url(key)}')


def cmd_edit(args):
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
            args.parser.error('--labels replaces the whole list, so combining it with '
                              '--add-label/--remove-label is contradictory. Pick one.')
        update['labels'] = label_ops

    if not fields and not update:
        args.parser.error('nothing to change — pass at least one field option')

    payload = {}
    if fields:
        payload['fields'] = fields
    if update:
        payload['update'] = update

    key = parse_key(args.target)
    send_json(f'/rest/api/2/issue/{key}', payload, method='PUT')

    changed = sorted(list(fields) + list(update))
    print(f'Updated {key}: {", ".join(changed)} — {browse_url(key)}')


# -- download --------------------------------------------------------------------

def cmd_download(args):
    dest = Path(args.dest).expanduser()
    dest.parent.mkdir(parents=True, exist_ok=True)

    data = fetch(args.url, accept='*/*')
    dest.write_bytes(data)
    print(f'Downloaded {len(data)} bytes to {dest}')


# -- command line ----------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog='jira.py',
        description='Read and write Jira Server / Data Center tickets over REST v2. '
                    'Env: JIRA_URL, JIRA_PERSONAL_TOKEN.',
        epilog='Exit codes: 1 setup or bad input, 2 HTTP or auth, 3 forbidden, '
               '4 not found, 5 network unreachable. There is no delete subcommand.')
    sub = parser.add_subparsers(dest='command', metavar='<subcommand>', required=True)

    p = sub.add_parser('fetch', help='print a ticket as Markdown; description and comments '
                                     'stay in Jira wiki markup')
    p.add_argument('target', help='ticket key or /browse/ URL')
    p.add_argument('--json', action='store_true',
                   help='print the raw REST response instead of Markdown')
    p.add_argument('--no-comments', action='store_true')
    p.add_argument('--comments', type=int, default=0,
                   help='keep only the N most recent comments')
    p.set_defaults(run=cmd_fetch, parser=p)

    p = sub.add_parser('search', help='search by JQL, or by text wrapped as text ~ "..."',
                       description='An argument that looks like JQL (contains =, ~, '
                                   'ORDER BY, AND/OR) is sent as-is; anything else is '
                                   'wrapped as a text search. One issue per line: '
                                   '<KEY>  [Status]  <summary>  —  <url>')
    p.add_argument('query', help='JQL, or plain text to search for')
    p.add_argument('--project', help='restrict to a project key, e.g. PROJ')
    p.add_argument('--limit', type=int, default=20)
    p.set_defaults(run=cmd_search, parser=p)

    p = sub.add_parser('transitions', help='list the workflow transitions available now',
                       description='One transition per line: <id>\\t<name>\\t->\\t'
                                   '<destination status>. Read this before transitioning; '
                                   'never assume an id.')
    p.add_argument('target', help='ticket key or browse URL')
    p.set_defaults(run=cmd_transitions, parser=p)

    p = sub.add_parser('transition', help='move a ticket to a status the workflow offers',
                       description='The second argument is the destination status '
                                   '(matched case-insensitively) or a numeric transition '
                                   'id. Prefer the name: it is checked against what the '
                                   'workflow offers, so it cannot invent a transition.')
    p.add_argument('target', help='ticket key or browse URL')
    p.add_argument('transition', help='destination status name, or transition id')
    p.set_defaults(run=cmd_transition, parser=p)

    p = sub.add_parser('comment', help='add a comment, in Jira wiki markup',
                       description='The body is Jira wiki markup, not Markdown: '
                                   '{code}...{code}, *bold*, h3. headings. Everyone on '
                                   'the ticket sees it: keep an automated comment to a '
                                   'line or two and say what happened, not how.')
    p.add_argument('target', help='ticket key or browse URL')
    p.add_argument('body', nargs='?', help='comment text (Jira wiki markup)')
    p.add_argument('--stdin', action='store_true',
                   help='read the comment body from stdin instead')
    p.set_defaults(run=cmd_comment, parser=p)

    p = sub.add_parser('create', help='create an issue; prints the new key and URL',
                       description='Projects differ in which fields their create screen '
                                   'requires. A 400 echoes Jira\'s own message naming the '
                                   'offending field; read it rather than retrying blind.')
    p.add_argument('--project', required=True, help='project key, e.g. PROJ')
    p.add_argument('--type', required=True, dest='issue_type',
                   help='issue type name, e.g. Bug, Story, Task')
    p.add_argument('--summary', required=True, help='the title')
    p.add_argument('--description', help='body, in Jira wiki markup')
    p.add_argument('--priority', help='priority name, e.g. Major')
    p.add_argument('--labels', help='comma-separated labels')
    p.add_argument('--components', help='comma-separated component names')
    p.add_argument('--assignee', help='username to assign to')
    p.add_argument('--parent', help='parent key, when creating a subtask')
    p.set_defaults(run=cmd_create, parser=p)

    p = sub.add_parser('edit', help='edit fields; status is not a field, use transition',
                       description='--labels replaces every label on the issue; '
                                   '--add-label / --remove-label leave the others alone. '
                                   'Status is NOT a field: use `transition`.')
    p.add_argument('target', help='ticket key or browse URL')
    p.add_argument('--summary', help='replace the title')
    p.add_argument('--description', help='replace the body (Jira wiki markup)')
    p.add_argument('--priority', help='priority name, e.g. Major')
    p.add_argument('--assignee', help='username; pass "none" to unassign')
    p.add_argument('--labels', help='comma-separated — REPLACES all labels')
    p.add_argument('--add-label', action='append', default=[], dest='add_labels',
                   help='add one label (repeatable)')
    p.add_argument('--remove-label', action='append', default=[], dest='remove_labels',
                   help='remove one label (repeatable)')
    p.set_defaults(run=cmd_edit, parser=p)

    p = sub.add_parser('download', help='download an attachment to a local path',
                       description='The content URL is the one `fetch` prints in its '
                                   'Attachments list.')
    p.add_argument('url', help='attachment content URL')
    p.add_argument('dest', help='where to write the file')
    p.set_defaults(run=cmd_download, parser=p)

    return parser


def main():
    args = build_parser().parse_args()
    args.run(args)


if __name__ == '__main__':
    main()
