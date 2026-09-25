#!/usr/bin/env python3
"""Add a comment to a Jira ticket.

Usage:
  add_comment.py <key-or-url> "<comment text>"
  add_comment.py <key-or-url> --stdin < body.txt

The body is Jira wiki markup, not Markdown — `{code}...{code}` for code blocks,
`*bold*`, `h3.` for headings. Plain prose passes through unchanged.

Comments are visible to everyone on the ticket. Keep automated ones to a line or
two, and say what happened rather than narrating the process.

Env: JIRA_URL, JIRA_PERSONAL_TOKEN (both required)
"""
import argparse
import sys

from _client import base_url, parse_key, send_json


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('key', help='ticket key or browse URL')
    parser.add_argument('body', nargs='?', help='comment text (Jira wiki markup)')
    parser.add_argument('--stdin', action='store_true',
                        help='read the comment body from stdin instead')
    args = parser.parse_args()

    body = sys.stdin.read() if args.stdin else args.body
    if not body or not body.strip():
        parser.error('empty comment body — pass text as an argument or use --stdin')

    key = parse_key(args.key)
    result = send_json(f'/rest/api/2/issue/{key}/comment', {'body': body})

    comment_id = (result or {}).get('id', '?')
    print(f'Commented on {key} (comment {comment_id}) — '
          f'{base_url()}/browse/{key}?focusedCommentId={comment_id}')


if __name__ == '__main__':
    main()
