#!/usr/bin/env python3
"""Fail when a tracked file names a specific project.

The tracked half of this repo describes the *shape* of a failure, never its coordinates:
no ticket keys, no PR numbers or commits in a provenance line, no private package scopes.
The coordinates belong in projects/<repository>/ENGINEERING.md, which is untracked
(see .agents/adr/0005-projects-folder.md).

Deliberately generic — a denylist of real repository names would itself be a project
reference, and a programme's name cannot be told from an ordinary word. Placeholders stay
allowed: PROJ-123, KEY-123, @scope/package, example.com.

Usage: scripts/check-portable.py        # exits 1 and lists every hit; 0 when clean
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = ('.md', '.sh', '.py', '.json', '.xhtml', '.txt', '.yml', '.yaml')

TICKET = re.compile(r'\b([A-Z]{2,5})-(\d{2,6})\b')
TICKET_OK = {'PROJ', 'KEY', 'UTF', 'ISO', 'SHA', 'HTTP', 'RFC', 'CVE', 'ES', 'TLS',
             'AES', 'RSA', 'MD', 'IEEE', 'ECMA'}

# Inside a provenance paragraph only: a PR number, or a hex token that has both a digit
# and a letter (a commit, not a word like "defaced" or a decimal id).
SOURCE = re.compile(r'^[_*]?Source:')
PR_OR_SHA = re.compile(r'#\d{2,}\b|\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b')

SCOPE = re.compile(r'@([a-z0-9][a-z0-9-]*)/[a-z0-9][a-z0-9._-]*')
SCOPE_OK = {'types', 'scope', 'design-system', 'example', 'anthropic-ai', 'org'}

LABELS = {
    'ticket': 'Ticket keys — use PROJ-123 as the placeholder:',
    'source': 'Source lines naming a PR or commit — the shape belongs here, the run in projects/:',
    'scope': 'Scoped package names — use @scope/... in examples:',
}


def tracked_text_files():
    out = subprocess.run(['git', 'ls-files', '-z'], cwd=REPO, capture_output=True,
                         text=True, check=True).stdout
    return [p for p in out.split('\0') if p and p.endswith(TEXT)]


def source_paragraph_lines(lines):
    """Yield (lineno, text) for every line of a paragraph that opens with a Source: line."""
    inside = False
    for n, line in enumerate(lines, 1):
        if SOURCE.match(line.strip()):
            inside = True
        elif inside and not line.strip():
            inside = False
        if inside:
            yield n, line


def main():
    hits = {key: [] for key in LABELS}
    for rel in tracked_text_files():
        with open(os.path.join(REPO, rel), encoding='utf-8', errors='replace') as fh:
            lines = fh.read().splitlines()
        for n, line in enumerate(lines, 1):
            if any(m.group(1) not in TICKET_OK for m in TICKET.finditer(line)):
                hits['ticket'].append(f'{rel}:{n}: {line.strip()}')
            if any(m.group(1) not in SCOPE_OK for m in SCOPE.finditer(line)):
                hits['scope'].append(f'{rel}:{n}: {line.strip()}')
        for n, line in source_paragraph_lines(lines):
            if PR_OR_SHA.search(line):
                hits['source'].append(f'{rel}:{n}: {line.strip()}')

    status = 0
    for key, found in hits.items():
        if not found:
            continue
        status = 1
        print(LABELS[key])
        print('\n'.join('  ' + h for h in found))
        print()
    if status == 0:
        print('portable: no project identifiers in tracked files')
    return status


if __name__ == '__main__':
    sys.exit(main())
