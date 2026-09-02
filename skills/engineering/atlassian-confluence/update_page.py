#!/usr/bin/env python3
"""Add or update a delimited section on a Confluence page, leaving the rest alone.

Usage:
  update_page.py <page-url-or-id> --marker ticket-report:PROJ-4821 \
      --heading "Verification — PROJ-4821" --body-file report.xhtml
  update_page.py <page-url-or-id> --marker ... --heading ... --stdin < report.xhtml
  update_page.py <page-url-or-id> --marker ... --heading ... --stdin --dry-run

The body must be Confluence **storage format** (XHTML), not Markdown. Markdown is
written to the page verbatim and renders as literal text.

The section is wrapped in comment markers:

  <!-- <marker> START -->  ...your content...  <!-- <marker> END -->

First run appends the block. Later runs replace only what sits between the
markers, so anything a colleague added elsewhere on the page survives.

Confluence has no append primitive — every update PUTs the whole body with an
incremented version. Two consequences this script handles rather than ignores:

  * A 409 means someone edited the page between our read and our write. It is
    reported, never retried; retrying would overwrite their edit.
  * If the markers are missing but a heading with the same text is already on the
    page, a human editing in the Confluence editor probably stripped the comments.
    Appending would silently duplicate the section, so this exits instead.

Env: CONFLUENCE_URL, CONFLUENCE_PERSONAL_TOKEN (both required)
"""
import argparse
import re
import sys

from _client import (EXIT_SETUP, base_url, die, get_json, page_url, resolve_page_id,
                     send_json)


def markers(name):
    return f'<!-- {name} START -->', f'<!-- {name} END -->'


def splice(body, name, heading, content):
    """Return the new page body, and what happened ('updated' | 'appended')."""
    start, end = markers(name)
    block = f'{start}\n{content}\n{end}'

    i, j = body.find(start), body.find(end)

    if i != -1 and j != -1 and j > i:
        return body[:i] + block + body[j + len(end):], 'updated'

    if i != -1 or j != -1:
        die(f'the page contains only one of the two {name!r} markers, so the section '
            f'boundaries are unclear. Fix the page by hand, then re-run.', EXIT_SETUP)

    # No markers. Before appending, make sure we are not duplicating a section whose
    # markers a human edit removed.
    if heading and re.search(re.escape(heading), body, re.I):
        die(f'no {name!r} markers found, but a section headed {heading!r} is already on '
            f'the page — the markers were probably stripped by an edit in the Confluence '
            f'editor. Appending would duplicate it. Re-add the markers around that '
            f'section by hand, or pass a different --marker.', EXIT_SETUP)

    sep = '' if body.endswith('\n') or not body else '\n'
    return f'{body}{sep}{block}', 'appended'


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('page', help='page URL or numeric page ID')
    parser.add_argument('--marker', required=True,
                        help='stable section name, e.g. ticket-report:PROJ-4821')
    parser.add_argument('--heading',
                        help='visible heading text, used to detect a duplicate section')
    parser.add_argument('--body-file', help='file holding the storage-format XHTML')
    parser.add_argument('--stdin', action='store_true', help='read the body from stdin')
    parser.add_argument('--dry-run', action='store_true',
                        help='report what would change; write nothing')
    args = parser.parse_args()

    if args.stdin:
        content = sys.stdin.read()
    elif args.body_file:
        with open(args.body_file, encoding='utf-8') as fh:
            content = fh.read()
    else:
        parser.error('pass --body-file or --stdin')

    if not content.strip():
        parser.error('empty body — nothing to write')

    page_id = resolve_page_id(args.page)
    page = get_json(f'/rest/api/content/{page_id}'
                    '?expand=body.storage,version,space,title')

    body = (((page.get('body') or {}).get('storage') or {}).get('value')) or ''
    version = ((page.get('version') or {}).get('number'))
    if version is None:
        die('the API response carried no version number, so a safe update is not '
            'possible.', EXIT_SETUP)

    new_body, action = splice(body, args.marker, args.heading, content)

    if args.dry_run:
        print(f'DRY RUN — would have {action} the {args.marker!r} section')
        print(f'  page:    {page.get("title")} ({page_id}) v{version}')
        print(f'  body:    {len(body)} chars -> {len(new_body)} chars')
        print(f'  url:     {page_url(page)}')
        return

    send_json(f'/rest/api/content/{page_id}', {
        'id': page_id,
        'type': 'page',
        'title': page.get('title'),
        'space': {'key': ((page.get('space') or {}).get('key'))},
        'body': {'storage': {'value': new_body, 'representation': 'storage'}},
        'version': {'number': version + 1,
                    'message': f'{args.marker} ({action} by agent)'},
    })

    print(f'{action.capitalize()} {args.marker!r} on "{page.get("title")}" '
          f'(v{version} -> v{version + 1}) — {page_url(page)}')


if __name__ == '__main__':
    main()
