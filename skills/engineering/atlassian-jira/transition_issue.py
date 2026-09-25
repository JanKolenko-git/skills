#!/usr/bin/env python3
"""Move a Jira ticket to a new status.

Usage:
  transition_issue.py <key-or-url> <destination-status-or-id>

The second argument is either the destination status you want (matched
case-insensitively) or a numeric transition id from get_transitions.py:

  transition_issue.py PROJ-1234 "In Review"
  transition_issue.py PROJ-1234 71

Prefer the name. A name is checked against what the workflow actually offers, so
it cannot invent a transition; a guessed id can. When a name matches nothing,
this prints the available transitions and exits non-zero rather than moving the
ticket somewhere merely adjacent.

Env: JIRA_URL, JIRA_PERSONAL_TOKEN (both required)
"""
import argparse

from _client import EXIT_SETUP, die, get_json, parse_key, send_json


def available(key):
    data = get_json(f'/rest/api/2/issue/{key}/transitions')
    return data.get('transitions', [])


def describe(transitions):
    return '\n'.join(
        f"  {t['id']}\t{t['name']}\t->\t{t.get('to', {}).get('name', '?')}"
        for t in transitions
    ) or '  (none — the workflow offers no transitions from the current status)'


def resolve(transitions, wanted):
    """Find the transition to run. Destination status first, then the
    transition's own name, then a unique substring match on the destination."""
    if wanted.isdigit():
        for t in transitions:
            if t['id'] == wanted:
                return t
        die(f'no transition with id {wanted}. Available:\n{describe(transitions)}',
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
        die(f'{wanted!r} matches more than one destination:\n{describe(partial)}\n'
            f'Re-run with the exact status name or the transition id.', EXIT_SETUP)

    die(f'no transition leads to {wanted!r} from the current status. Available:\n'
        f'{describe(transitions)}', EXIT_SETUP)


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('key', help='ticket key or browse URL')
    parser.add_argument('transition', help='destination status name, or transition id')
    args = parser.parse_args()

    key = parse_key(args.key)
    chosen = resolve(available(key), args.transition)

    send_json(f'/rest/api/2/issue/{key}/transitions',
              {'transition': {'id': chosen['id']}})

    dest = chosen.get('to', {}).get('name', '?')
    print(f'{key} -> {dest}  (via "{chosen["name"]}", id {chosen["id"]})')


if __name__ == '__main__':
    main()
