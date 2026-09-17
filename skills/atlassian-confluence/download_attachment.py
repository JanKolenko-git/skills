#!/usr/bin/env python3
"""Download a Confluence attachment to a local path.

Usage:
  download_attachment.py <download-url> <dest-path>

Get the download URL from list_attachments.py. Relative URLs (as returned by the
REST API) are resolved against CONFLUENCE_URL.

Env: CONFLUENCE_URL, CONFLUENCE_PERSONAL_TOKEN (both required)
"""
import argparse
from pathlib import Path

from _client import fetch


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('url', help='attachment download URL')
    parser.add_argument('dest', help='where to write the file')
    args = parser.parse_args()

    dest = Path(args.dest).expanduser()
    dest.parent.mkdir(parents=True, exist_ok=True)

    data = fetch(args.url, accept='*/*')
    dest.write_bytes(data)
    print(f'Downloaded {len(data)} bytes to {dest}')


if __name__ == '__main__':
    main()
