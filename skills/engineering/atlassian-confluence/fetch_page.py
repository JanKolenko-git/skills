#!/usr/bin/env python3
"""Fetch a Confluence page and print it as Markdown on stdout.

Usage:
  fetch_page.py <page-url-or-id> [--format view|storage] [--json] [--body-only]

Accepts any of these as <page-url-or-id>:
  https://confluence.example.com/spaces/ENG/pages/1778320229/Some+Title
  https://confluence.example.com/pages/viewpage.action?pageId=1778320229
  https://confluence.example.com/display/ENG/Some+Title
  1778320229

Env: CONFLUENCE_URL, CONFLUENCE_PERSONAL_TOKEN (both required)
"""
import argparse
import json
import sys

from _client import get_json, page_url, resolve_page_id
from _markdown import html_to_markdown

EXPAND = ('body.view,body.storage,version,space,ancestors,'
          'children.attachment,metadata.labels')


def _size(num):
    if num < 1024:
        return f'{num} B'
    if num < 1024 * 1024:
        return f'{num / 1024:.0f} KB'
    return f'{num / (1024 * 1024):.1f} MB'


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('target', help='page URL or numeric page ID')
    parser.add_argument('--format', choices=('view', 'storage'), default='view',
                        help='view = macros rendered, converted to Markdown (default); '
                             'storage = raw storage-format XHTML, printed unconverted')
    parser.add_argument('--json', action='store_true',
                        help='print the raw REST response instead of Markdown')
    parser.add_argument('--body-only', action='store_true',
                        help='omit the metadata header')
    args = parser.parse_args()

    page_id = resolve_page_id(args.target)
    page = get_json(f'/rest/api/content/{page_id}?expand={EXPAND}')

    if args.json:
        print(json.dumps(page, indent=2))
        return

    body = ((page.get('body') or {}).get(args.format) or {}).get('value', '')
    fallback_used = False
    used_format = args.format
    if not body.strip():
        other = 'storage' if args.format == 'view' else 'view'
        body = ((page.get('body') or {}).get(other) or {}).get('value', '')
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
    attachments = (((page.get('children') or {}).get('attachment') or {}).get('results') or [])
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
    if attachments:
        listed = ', '.join(
            f'{a.get("title")} ({(a.get("metadata") or {}).get("mediaType", "?")}'
            f', {_size(((a.get("extensions") or {}).get("fileSize")) or 0)})'
            for a in attachments)
        lines.append(f'- **Attachments ({len(attachments)}):** {listed}')
        lines.append('  Use list_attachments.py / download_attachment.py to read them.')
    if fallback_used:
        lines.append(f'- **Note:** `{args.format}` body was empty; showed the other format instead.')

    lines += ['', '---', '', rendered]
    sys.stdout.write('\n'.join(lines))


if __name__ == '__main__':
    main()
