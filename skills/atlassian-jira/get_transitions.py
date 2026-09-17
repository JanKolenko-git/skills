#!/usr/bin/env python3
"""List the workflow transitions available on a Jira ticket right now.

Usage:
  get_transitions.py <key-or-url>

Prints one transition per line:  <id>\t<name>\t->\t<destination status>

Which transitions exist depends on the ticket's current status and the project's
workflow, so a status that was reachable yesterday may not be reachable today.
Read this before transitioning; never assume an id.

Env: JIRA_URL, JIRA_PERSONAL_TOKEN (both required)
"""
import argparse

from _client import get_json, parse_key


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('key', help='ticket key or browse URL')
    args = parser.parse_args()

    key = parse_key(args.key)
    data = get_json(f'/rest/api/2/issue/{key}/transitions')
    transitions = data.get('transitions', [])

    if not transitions:
        print(f'{key}: no transitions available from its current status.')
        return

    for t in transitions:
        dest = t.get('to', {}).get('name', '?')
        print(f"{t['id']}\t{t['name']}\t->\t{dest}")


if __name__ == '__main__':
    main()
