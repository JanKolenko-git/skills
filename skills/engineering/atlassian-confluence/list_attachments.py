#!/usr/bin/env python3
"""List a Confluence page's attachments with their download URLs.

Usage:
  list_attachments.py <page-url-or-id>

Prints one attachment per line:  <filename>  <media-type>  <size>  <download-url>

Env: CONFLUENCE_URL, CONFLUENCE_PERSONAL_TOKEN (both required)
"""
import argparse

from _client import base_url, get_json, resolve_page_id


def _size(num):
    if num < 1024:
        return f'{num} B'
    if num < 1024 * 1024:
        return f'{num / 1024:.0f} KB'
    return f'{num / (1024 * 1024):.1f} MB'


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('target', help='page URL or numeric page ID')
    args = parser.parse_args()

    page_id = resolve_page_id(args.target)
    results = get_json(
        f'/rest/api/content/{page_id}/child/attachment?limit=100'
    ).get('results', [])

    if not results:
        print('No attachments on this page.')
        return

    for item in results:
        media = (item.get('metadata') or {}).get('mediaType', '?')
        size = _size(((item.get('extensions') or {}).get('fileSize')) or 0)
        link = (item.get('_links') or {}).get('download', '')
        if link and not link.startswith('http'):
            link = f'{base_url()}{link}'
        print(f'{item.get("title")}\t{media}\t{size}\t{link}')


if __name__ == '__main__':
    main()
