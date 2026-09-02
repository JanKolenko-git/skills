#!/usr/bin/env python3
"""Search Jira for issues, by JQL or by free text.

Usage:
  search_issues.py "<jql-or-text>" [--project PROJ] [--limit 20]

An argument that looks like JQL (contains =, ~, "ORDER BY", AND/OR) is sent as-is;
anything else is wrapped as a text search.

Prints one issue per line:  <KEY>  [Status]  <summary>  —  <url>

Env: JIRA_URL, JIRA_PERSONAL_TOKEN (both required)
"""
import argparse
import re
import urllib.parse

from _client import base_url, get_json


def looks_like_jql(text):
    return bool(re.search(r'(=|~|\bORDER\s+BY\b|\bAND\b|\bOR\b|\bIN\b\s*\()',
                          text, re.I))


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('query', help='JQL, or plain text to search for')
    parser.add_argument('--project', help='restrict to a project key, e.g. PROJ')
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()

    if looks_like_jql(args.query):
        jql = args.query
    else:
        needle = args.query.replace('\\', '\\\\').replace('"', '\\"')
        jql = f'text ~ "{needle}"'

    if args.project and 'project' not in jql.lower():
        jql = f'project = "{args.project}" AND ({jql})'
    if 'order by' not in jql.lower():
        jql += ' ORDER BY updated DESC'

    url = (f'/rest/api/2/search?jql={urllib.parse.quote(jql)}'
           f'&maxResults={args.limit}&fields=summary,status')

    issues = get_json(url).get('issues', [])
    if not issues:
        print(f'No issues matched. (JQL: {jql})')
        return

    for issue in issues:
        fields = issue.get('fields') or {}
        status = ((fields.get('status') or {}).get('name')) or '?'
        key = issue.get('key')
        print(f'{key}  [{status}]  {fields.get("summary", "")}  '
              f'—  {base_url()}/browse/{key}')


if __name__ == '__main__':
    main()
