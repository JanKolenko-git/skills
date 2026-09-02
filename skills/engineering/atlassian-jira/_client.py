"""Shared HTTP/auth helpers for the jira skill.

Targets Jira Server / Data Center: REST v2, wiki markup, and a personal access
token sent as a Bearer credential. Jira Cloud is a different API (v3, ADF) with
different auth, and will not work here.

Reads JIRA_URL and JIRA_PERSONAL_TOKEN from the environment.
Never hardcode a token here — this file is safe to read and share.
"""
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

# Exit codes, so callers can distinguish "no access" from "broken setup".
EXIT_SETUP = 1
EXIT_HTTP = 2
EXIT_FORBIDDEN = 3
EXIT_NOTFOUND = 4
EXIT_NETWORK = 5


def die(msg, code=EXIT_SETUP):
    print(f'Error: {msg}', file=sys.stderr)
    sys.exit(code)


def base_url():
    url = os.environ.get('JIRA_URL', '')
    if not url:
        die('JIRA_URL is not set. Point it at your Jira Data Center instance, '
            'e.g. export JIRA_URL=https://jira.example.com (in ~/.zshenv).')
    return url.rstrip('/')


def _token():
    token = os.environ.get('JIRA_PERSONAL_TOKEN', '')
    if not token:
        die('JIRA_PERSONAL_TOKEN is not set. In Jira, open the profile menu -> '
            'Personal Access Tokens, create one, then export it (e.g. in ~/.zshenv).')
    return token


def _ssl_context():
    # Verification stays on by default. Set JIRA_INSECURE_TLS=1 only if a
    # TLS-inspecting corporate proxy breaks an otherwise valid chain.
    if os.environ.get('JIRA_INSECURE_TLS') == '1':
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return ssl.create_default_context()


def _reject_sso_page(final_url, body, accept):
    """Catch an SSO interception, which arrives as HTTP 200 and would otherwise
    surface as a JSON parse error several frames away from the real cause.

    When the corporate edge is in the way it answers *every* REST call with the
    Microsoft login page, so this is not an auth failure the token can fix.
    """
    if 'login.microsoftonline.com' in final_url or '/openid-login' in final_url:
        die('redirected to the Microsoft SSO login page instead of reaching the Jira '
            'API, so the request never arrived. This is a network problem, not a token '
            'problem — connect to the corporate network or VPN and retry. If it '
            'persists while on VPN, JIRA_PERSONAL_TOKEN may have been revoked; create a '
            'fresh one in Jira.', EXIT_HTTP)
    # Only when JSON was asked for: an attachment may legitimately be HTML.
    if 'json' in accept and body[:512].lstrip()[:1] == b'<':
        die(f'expected JSON from {final_url} but got an HTML page — most likely a login '
            f'or captive portal in front of Jira rather than Jira itself.', EXIT_HTTP)


def fetch(url, accept='application/json', timeout=60):
    """GET a URL with the PAT attached. Returns raw bytes; exits on failure."""
    if not url.startswith('http'):
        url = f'{base_url()}{url}'

    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {_token()}',
        'Accept': accept,
    })

    try:
        with urllib.request.urlopen(req, context=_ssl_context(), timeout=timeout) as r:
            body = r.read()
            _reject_sso_page(r.geturl(), body, accept)
            return body
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode('utf-8', 'replace')[:400]
        except Exception:
            detail = ''
        if e.code == 401:
            die('HTTP 401 — JIRA_PERSONAL_TOKEN was rejected. It has probably expired; '
                'create a fresh one in Jira.', EXIT_HTTP)
        if e.code == 403:
            die(f'HTTP 403 — no access to {url}', EXIT_FORBIDDEN)
        if e.code == 404:
            die(f'HTTP 404 — not found: {url}', EXIT_NOTFOUND)
        die(f'HTTP {e.code} — {detail}', EXIT_HTTP)
    except urllib.error.URLError as e:
        die(f'cannot reach {url} ({e.reason}). Is the host right, and are you on '
            f'the network or VPN it sits behind?', EXIT_NETWORK)


def get_json(path):
    return json.loads(fetch(path))


def send_json(path, payload, method='POST', timeout=60):
    """POST/PUT a JSON body with the PAT attached.

    Returns the decoded response, or None when Jira answers with an empty body —
    transitions and field edits both reply 204 No Content on success.

    Writes are deliberately kept in this one function so there is a single place
    to audit what can change a ticket.
    """
    if not url_is_absolute(path):
        path = f'{base_url()}{path}'

    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(path, data=body, method=method, headers={
        'Authorization': f'Bearer {_token()}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    })

    try:
        with urllib.request.urlopen(req, context=_ssl_context(), timeout=timeout) as r:
            raw = r.read()
            _reject_sso_page(r.geturl(), raw, 'application/json')
            if not raw.strip():
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode('utf-8', 'replace')[:400]
        except Exception:
            detail = ''
        if e.code == 401:
            die('HTTP 401 — JIRA_PERSONAL_TOKEN was rejected. It has probably expired; '
                'create a fresh one in Jira.', EXIT_HTTP)
        if e.code == 403:
            die(f'HTTP 403 — the token is valid but this account may not change '
                f'{path}. {detail}', EXIT_FORBIDDEN)
        if e.code == 404:
            die(f'HTTP 404 — not found: {path}', EXIT_NOTFOUND)
        # 400 on a write usually means a field the screen does not accept, and the
        # body says which — so pass it through rather than flattening it.
        die(f'HTTP {e.code} — {detail}', EXIT_HTTP)
    except urllib.error.URLError as e:
        die(f'cannot reach {path} ({e.reason}). Is the host right, and are you on '
            f'the network or VPN it sits behind?', EXIT_NETWORK)


def url_is_absolute(value):
    return value.startswith('http://') or value.startswith('https://')


def parse_key(arg):
    """Extract a ticket key from a browse URL, an issue URL, or a bare key."""
    arg = arg.strip()
    if re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*-\d+', arg):
        return arg.upper()

    match = re.search(r'/browse/([A-Za-z][A-Za-z0-9_]*-\d+)', arg)
    if match:
        return match.group(1).upper()

    parsed = urllib.parse.urlparse(arg if '://' in arg else f'https://{arg}')
    query = urllib.parse.parse_qs(parsed.query)
    for name in ('selectedIssue', 'issueKey', 'key'):
        if name in query:
            return query[name][0].upper()

    match = re.search(r'([A-Za-z][A-Za-z0-9_]*-\d+)', arg)
    if match:
        return match.group(1).upper()

    die(f'could not find a ticket key in {arg!r}. Pass a key like PROJ-1234 or a '
        f'/browse/ URL.')


def browse_url(key):
    return f'{base_url()}/browse/{key}'
