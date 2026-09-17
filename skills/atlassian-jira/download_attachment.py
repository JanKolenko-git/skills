#!/usr/bin/env python3
"""Download a Jira attachment to a local path.

Usage:
  download_attachment.py <content-url> <dest-path>

The content URL is the `content` field of an attachment, which fetch_ticket.py
prints in its Attachments list.

Env: JIRA_URL, JIRA_PERSONAL_TOKEN (both required)
"""
import argparse
from pathlib import Path

from _client import fetch


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('url', help='attachment content URL')
    parser.add_argument('dest', help='where to write the file')
    args = parser.parse_args()

    dest = Path(args.dest).expanduser()
    dest.parent.mkdir(parents=True, exist_ok=True)

    data = fetch(args.url, accept='*/*')
    dest.write_bytes(data)
    print(f'Downloaded {len(data)} bytes to {dest}')


if __name__ == '__main__':
    main()
