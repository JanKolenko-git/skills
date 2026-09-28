#!/usr/bin/env python3
"""Read and update Confluence Server / Data Center pages over /rest/api/content.

  confluence.py fetch <page-url-or-id> [--format view|storage] [--json] [--body-only]
  confluence.py search "<query>" [--space ENG] [--title-only] [--limit 10]
  confluence.py download <download-url> <dest-path>
  confluence.py update-section <page-url-or-id> --marker <name> [--heading <text>]
                (--body-file <file> | --stdin) [--dry-run]

<page-url-or-id> is a numeric page id or any URL shape Confluence hands out:
  https://confluence.example.com/spaces/ENG/pages/1778320229/Some+Title
  https://confluence.example.com/pages/viewpage.action?pageId=1778320229
  https://confluence.example.com/display/ENG/Some+Title
`--help` on a subcommand lists its options. There is no delete subcommand.

Env: CONFLUENCE_URL, CONFLUENCE_PERSONAL_TOKEN (both required)
"""
import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

from _client import EXIT_NOTFOUND, EXIT_SETUP, base_url, die, fetch, get_json, send_json
from _markdown import html_to_markdown

# One body format per request: the other is fetched only when the first comes back
# empty, so a large page costs one body, not two.
EXPAND = 'version,space,ancestors,children.attachment,metadata.labels'


# -- targets ---------------------------------------------------------------------

def parse_target(arg):
    """Turn a page URL or bare ID into ('id', <id>) or ('title', (space, title))."""
    arg = arg.strip()
    if re.fullmatch(r'\d+', arg):
        return ('id', arg)

    parsed = urllib.parse.urlparse(arg if '://' in arg else f'https://{arg}')
    query = urllib.parse.parse_qs(parsed.query)

    if 'pageId' in query:
        return ('id', query['pageId'][0])

    parts = [p for p in parsed.path.split('/') if p]

    for i, part in enumerate(parts):
        if part == 'pages' and i + 1 < len(parts) and re.fullmatch(r'\d+', parts[i + 1]):
            return ('id', parts[i + 1])

    if 'display' in parts:
        i = parts.index('display')
        if len(parts) >= i + 3:
            space = urllib.parse.unquote(parts[i + 1])
            title = urllib.parse.unquote_plus(parts[i + 2])
            return ('title', (space, title))

    die(f'could not work out a page from {arg!r}. Pass a page URL or a numeric page ID.')


def resolve_page_id(arg):
    """Resolve any accepted target to a numeric page ID."""
    kind, value = parse_target(arg)
    if kind == 'id':
        return value

    space, title = value
    url = (f'/rest/api/content?spaceKey={urllib.parse.quote(space)}'
           f'&title={urllib.parse.quote(title)}&limit=1')
    results = get_json(url).get('results', [])
    if not results:
        die(f'no page titled {title!r} in space {space}.', EXIT_NOTFOUND)
    return results[0]['id']


def page_url(page):
    """Absolute browser URL for a content object from the REST API."""
    webui = ((page.get('_links') or {}).get('webui')) or ''
    if webui:
        return f'{base_url()}{webui}'
    return f'{base_url()}/pages/viewpage.action?pageId={page.get("id")}'


def _download_url(attachment):
    """Absolute download URL of an attachment content object; the API returns it
    relative to the instance."""
    link = ((attachment.get('_links') or {}).get('download')) or ''
    if link and not link.startswith('http'):
        link = f'{base_url()}{link}'
    return link


def _size(num):
    if num < 1024:
        return f'{num} B'
    if num < 1024 * 1024:
        return f'{num / 1024:.0f} KB'
    return f'{num / (1024 * 1024):.1f} MB'


# -- fetch -----------------------------------------------------------------------

def _body(page, fmt):
    return ((page.get('body') or {}).get(fmt) or {}).get('value', '')


def cmd_fetch(args):
    page_id = resolve_page_id(args.target)
    page = get_json(f'/rest/api/content/{page_id}?expand=body.{args.format},{EXPAND}')

    if args.json:
        print(json.dumps(page, indent=2))
        return

    body = _body(page, args.format)
    fallback_used = False
    used_format = args.format
    if not body.strip():
        other = 'storage' if args.format == 'view' else 'view'
        body = _body(get_json(f'/rest/api/content/{page_id}?expand=body.{other}'), other)
        fallback_used = bool(body.strip())
        if fallback_used:
            used_format = other

    # storage is requested when the caller intends to rewrite the page and needs the exact
    # macro source; converting it to Markdown silently destroys every <ac:...> element.
    rendered = body if used_format == 'storage' else html_to_markdown(body)

    if args.body_only:
        print(rendered, end='')
        return

    space = page.get('space') or {}
    version = page.get('version') or {}
    ancestors = page.get('ancestors') or []
    attachments = ((page.get('children') or {}).get('attachment') or {})
    listed = attachments.get('results') or []
    labels = (((page.get('metadata') or {}).get('labels') or {}).get('results') or [])

    lines = [f'# {page.get("title", "(untitled)")}', '']
    lines.append(f'- **Page ID:** {page_id}')
    lines.append(f'- **Space:** {space.get("key", "?")}'
                 + (f' — {space["name"]}' if space.get('name') else ''))
    if ancestors:
        trail = ' › '.join(a.get('title', '?') for a in ancestors)
        lines.append(f'- **Breadcrumb:** {trail}')
    if version:
        by = ((version.get('by') or {}).get('displayName')) or '?'
        when = (version.get('when') or '')[:10]
        lines.append(f'- **Version:** {version.get("number", "?")} — last updated {when} by {by}')
    if labels:
        lines.append('- **Labels:** ' + ', '.join(l.get('name', '') for l in labels))
    lines.append(f'- **URL:** {page_url(page)}')
    if listed:
        lines.append(f'- **Attachments ({len(listed)}):**')
        for item in listed:
            media = (item.get('metadata') or {}).get('mediaType', '?')
            size = _size(((item.get('extensions') or {}).get('fileSize')) or 0)
            lines.append(f'  - {item.get("title")} ({media}, {size}) — {_download_url(item)}')
        if (attachments.get('_links') or {}).get('next'):
            lines.append(f'  - … more attachments than the {len(listed)} listed')
    if fallback_used:
        lines.append(f'- **Note:** `{args.format}` body was empty; showed the other format instead.')

    lines += ['', '---', '', rendered]
    sys.stdout.write('\n'.join(lines))


# -- search ----------------------------------------------------------------------

def cmd_search(args):
    # CQL string literals are double-quoted, so escape any quotes in the query.
    needle = args.query.replace('\\', '\\\\').replace('"', '\\"')
    clauses = ['type=page']
    if args.title_only:
        clauses.append(f'title ~ "{needle}"')
    else:
        clauses.append(f'(title ~ "{needle}" OR text ~ "{needle}")')
    if args.space:
        clauses.append(f'space="{args.space}"')

    cql = ' AND '.join(clauses) + ' ORDER BY lastmodified DESC'
    url = (f'/rest/api/content/search?cql={urllib.parse.quote(cql)}'
           f'&limit={args.limit}&expand=space,version')

    results = get_json(url).get('results', [])
    if not results:
        print('No pages matched.')
        return

    for page in results:
        space = (page.get('space') or {}).get('key', '?')
        print(f'{page.get("id")}  [{space}]  {page.get("title")}  —  {page_url(page)}')


# -- download --------------------------------------------------------------------

def cmd_download(args):
    dest = Path(args.dest).expanduser()
    dest.parent.mkdir(parents=True, exist_ok=True)

    data = fetch(args.url, accept='*/*')
    dest.write_bytes(data)
    print(f'Downloaded {len(data)} bytes to {dest}')


# -- update-section --------------------------------------------------------------

def _markers(name):
    return f'<!-- {name} START -->', f'<!-- {name} END -->'


def _splice(body, name, heading, block):
    """Return the new page body, what happened ('updated' | 'appended'), and the
    section the block replaces, or None when it is appended.

    Confluence has no append primitive: every update PUTs the whole body with an
    incremented version. So the section is delimited by comment markers, and only
    what sits between them is replaced; anything a colleague added elsewhere on the
    page survives. Two cases stop rather than guess: only one marker present, and
    no markers but the heading already on the page (a human editing in the
    Confluence editor probably stripped the comments; appending would duplicate
    the section).
    """
    start, end = _markers(name)
    i, j = body.find(start), body.find(end)

    if i != -1 and j != -1 and j > i:
        current = body[i:j + len(end)]
        return body[:i] + block + body[j + len(end):], 'updated', current

    if i != -1 or j != -1:
        die(f'the page contains only one of the two {name!r} markers, so the section '
            f'boundaries are unclear. Fix the page by hand, then re-run.', EXIT_SETUP)

    if heading and re.search(re.escape(heading), body, re.I):
        die(f'no {name!r} markers found, but a section headed {heading!r} is already on '
            f'the page — the markers were probably stripped by an edit in the Confluence '
            f'editor. Appending would duplicate it. Re-add the markers around that '
            f'section by hand, or pass a different --marker.', EXIT_SETUP)

    sep = '' if body.endswith('\n') or not body else '\n'
    return f'{body}{sep}{block}', 'appended', None


def cmd_update_section(args):
    if args.stdin:
        content = sys.stdin.read()
    elif args.body_file:
        with open(args.body_file, encoding='utf-8') as fh:
            content = fh.read()
    else:
        args.parser.error('pass --body-file or --stdin')

    if not content.strip():
        args.parser.error('empty body — nothing to write')

    page_id = resolve_page_id(args.page)
    page = get_json(f'/rest/api/content/{page_id}'
                    '?expand=body.storage,version,space,title')

    body = (((page.get('body') or {}).get('storage') or {}).get('value')) or ''
    version = ((page.get('version') or {}).get('number'))
    if version is None:
        die('the API response carried no version number, so a safe update is not '
            'possible.', EXIT_SETUP)

    start, end = _markers(args.marker)
    block = f'{start}\n{content}\n{end}'
    new_body, action, current = _splice(body, args.marker, args.heading, block)

    if args.dry_run:
        # The gate needs the artefact on screen: the section as it would be written
        # and the one it replaces, not a character count.
        verb, joiner = ('update', 'on') if current is not None else ('append', 'to')
        print(f'DRY RUN: would {verb} {args.marker!r} {joiner} "{page.get("title")}" '
              f'({page_id}, v{version} -> v{version + 1})')
        if current is not None:
            print('--- current section')
            print(current)
        print('+++ new section')
        print(block)
        print(page_url(page))
        return

    # A 409 here means the page moved between this read and the write; the client
    # reports it and never retries with a bumped number, which would overwrite the edit.
    send_json(f'/rest/api/content/{page_id}', {
        'id': page_id,
        'type': 'page',
        'title': page.get('title'),
        'space': {'key': ((page.get('space') or {}).get('key'))},
        'body': {'storage': {'value': new_body, 'representation': 'storage'}},
        'version': {'number': version + 1,
                    'message': f'{args.marker} ({action} by agent)'},
    }, method='PUT')

    print(f'{action.capitalize()} {args.marker!r} on "{page.get("title")}" '
          f'(v{version} -> v{version + 1}) — {page_url(page)}')


# -- command line ----------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog='confluence.py',
        description='Read and update Confluence Server / Data Center pages over '
                    '/rest/api/content. Env: CONFLUENCE_URL, CONFLUENCE_PERSONAL_TOKEN.',
        epilog='Exit codes: 1 setup or bad input, 2 HTTP or auth, 3 forbidden, '
               '4 not found, 5 network unreachable. There is no delete subcommand.')
    sub = parser.add_subparsers(dest='command', metavar='<subcommand>', required=True)

    p = sub.add_parser('fetch', help='print a page as Markdown, with a metadata header '
                                     'that lists attachments and their download URLs')
    p.add_argument('target', help='page URL or numeric page ID')
    p.add_argument('--format', choices=('view', 'storage'), default='view',
                   help='view = macros rendered, converted to Markdown (default); '
                        'storage = raw storage-format XHTML, printed unconverted')
    p.add_argument('--json', action='store_true',
                   help='print the raw REST response (its body in --format) instead of '
                        'Markdown')
    p.add_argument('--body-only', action='store_true', help='omit the metadata header')
    p.set_defaults(run=cmd_fetch, parser=p)

    p = sub.add_parser('search', help='search pages by title or body text',
                       description='One result per line: <page-id>  [SPACE]  <title>  —  '
                                   '<url>')
    p.add_argument('query', help='text to search for')
    p.add_argument('--space', help='restrict to a space key, e.g. ENG')
    p.add_argument('--title-only', action='store_true',
                   help='match titles only (fewer, sharper hits)')
    p.add_argument('--limit', type=int, default=10)
    p.set_defaults(run=cmd_search, parser=p)

    p = sub.add_parser('download', help='download an attachment to a local path',
                       description='The download URL is the one `fetch` prints in its '
                                   'Attachments list; a relative one is resolved against '
                                   'CONFLUENCE_URL.')
    p.add_argument('url', help='attachment download URL')
    p.add_argument('dest', help='where to write the file')
    p.set_defaults(run=cmd_download, parser=p)

    p = sub.add_parser('update-section',
                       help='add or replace one marker-delimited section, leaving the '
                            'rest of the page alone',
                       description='The body must be Confluence storage format (XHTML), '
                                   'not Markdown; Markdown is written verbatim and renders '
                                   'as literal text. The section is wrapped in '
                                   '<!-- <marker> START --> ... <!-- <marker> END -->: the '
                                   'first run appends it, later runs replace only what '
                                   'sits between the markers. --dry-run first: it '
                                   'prints the section as it would be written and the '
                                   'one it replaces.')
    p.add_argument('page', help='page URL or numeric page ID')
    p.add_argument('--marker', required=True,
                   help='stable section name, e.g. ticket-report:PROJ-4821')
    p.add_argument('--heading',
                   help='visible heading text, used to detect a duplicate section')
    p.add_argument('--body-file', help='file holding the storage-format XHTML')
    p.add_argument('--stdin', action='store_true', help='read the body from stdin')
    p.add_argument('--dry-run', action='store_true',
                   help='report what would change; write nothing')
    p.set_defaults(run=cmd_update_section, parser=p)

    return parser


def main():
    args = build_parser().parse_args()
    args.run(args)


if __name__ == '__main__':
    main()
