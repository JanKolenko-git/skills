#!/usr/bin/env python3
"""Search Confluence for pages by title or body text.

Usage:
  search_pages.py "<query>" [--space ENG] [--title-only] [--limit 10]

Prints one result per line:  <page-id>  [SPACE]  <title>  —  <url>

Env: CONFLUENCE_URL, CONFLUENCE_PERSONAL_TOKEN (both required)
"""
import argparse
import urllib.parse

from _client import get_json, page_url


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('query', help='text to search for')
    parser.add_argument('--space', help='restrict to a space key, e.g. ENG')
    parser.add_argument('--title-only', action='store_true',
                        help='match titles only (fewer, sharper hits)')
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()

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


if __name__ == '__main__':
    main()
