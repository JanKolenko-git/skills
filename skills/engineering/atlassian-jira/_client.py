"""Shared HTTP and auth helpers for the Atlassian skills.

Targets Jira or Confluence Server / Data Center with a personal access token sent
as a Bearer credential. Atlassian Cloud is a different API with different auth,
and will not work here.

Reads <PRODUCT>_URL and <PRODUCT>_PERSONAL_TOKEN from the environment. Never
hardcode a token here: this file is safe to read and share.

This file is identical in atlassian-jira and atlassian-confluence except for the
PRODUCT line, on purpose: a skill never imports across folders. A fix here goes
into both copies, and `diff` proves they still match.
"""
import json
import os
import ssl
import sys
import urllib.error
import urllib.request

PRODUCT = 'Jira'

ENV_URL = f'{PRODUCT.upper()}_URL'
ENV_TOKEN = f'{PRODUCT.upper()}_PERSONAL_TOKEN'

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
    url = os.environ.get(ENV_URL, '')
    if not url:
        die(f'{ENV_URL} is not set. Point it at your {PRODUCT} Data Center instance, '
            f'e.g. export {ENV_URL}=https://{PRODUCT.lower()}.example.com (in ~/.zshenv).')
    return url.rstrip('/')


def _token():
    token = os.environ.get(ENV_TOKEN, '')
    if not token:
        die(f'{ENV_TOKEN} is not set. In {PRODUCT}, open the profile menu -> Personal '
            f'Access Tokens, create one, then export it (e.g. in ~/.zshenv). Tokens are '
            f'per product: a token for the other product gets a 401 here.')
    return token


def absolute(url):
    """A path becomes a URL on the instance; an absolute URL passes through."""
    if url.startswith('http://') or url.startswith('https://'):
        return url
    return f'{base_url()}{url}'


def _reject_sso_page(final_url, body, accept):
    """Catch an SSO interception, which arrives as HTTP 200 and would otherwise
    surface as a JSON parse error several frames away from the real cause.

    When the corporate edge is in the way it answers *every* REST call with the
    Microsoft login page, so this is not an auth failure the token can fix.
    """
    if 'login.microsoftonline.com' in final_url or '/openid-login' in final_url:
        die(f'redirected to the Microsoft SSO login page instead of reaching the {PRODUCT} '
            f'API, so the request never arrived. This is a network problem, not a token '
            f'problem — connect to the corporate network or VPN and retry. If it persists '
            f'while on VPN, {ENV_TOKEN} may have been revoked; create a fresh one in '
            f'{PRODUCT}.', EXIT_HTTP)
    # Only when JSON was asked for: an attachment may legitimately be HTML.
    if 'json' in accept and body[:512].lstrip()[:1] == b'<':
        die(f'expected JSON from {final_url} but got an HTML page — most likely a login '
            f'or captive portal in front of {PRODUCT} rather than {PRODUCT} itself.',
            EXIT_HTTP)


def _request(url, accept, data=None, method=None, timeout=60):
    """Every HTTP call goes through here: the PAT header, the SSO check, and one
    mapping from HTTP status to exit code. Returns the raw body; exits on failure.
    """
    headers = {'Authorization': f'Bearer {_token()}', 'Accept': accept}
    writing = data is not None
    if writing:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, method=method, headers=headers)

    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
            body = r.read()
            _reject_sso_page(r.geturl(), body, accept)
            return body
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode('utf-8', 'replace')[:400]
        except Exception:
            detail = ''
        if e.code == 401:
            die(f'HTTP 401 — {ENV_TOKEN} was rejected. It has probably expired; create a '
                f'fresh one in {PRODUCT}.', EXIT_HTTP)
        if e.code == 403 and writing:
            die(f'HTTP 403 — the token is valid but this account may not change {url}. '
                f'{detail}', EXIT_FORBIDDEN)
        if e.code == 403:
            die(f'HTTP 403 — no access to {url}', EXIT_FORBIDDEN)
        if e.code == 404:
            die(f'HTTP 404 — not found: {url}', EXIT_NOTFOUND)
        if e.code == 409:
            die('HTTP 409 — it changed since it was read, so writing now would overwrite '
                'someone else\'s edit. Re-read it and apply the update again.', EXIT_HTTP)
        # A 400 on a write usually names the field the screen does not accept, in the
        # body, so it is passed through rather than flattened.
        die(f'HTTP {e.code} — {detail}', EXIT_HTTP)
    except urllib.error.URLError as e:
        die(f'cannot reach {url} ({e.reason}). Is the host right, and are you on the '
            f'network or VPN it sits behind?', EXIT_NETWORK)


def fetch(url, accept='application/json', timeout=60):
    """GET a path or URL with the PAT attached. Returns raw bytes; exits on failure."""
    return _request(absolute(url), accept, timeout=timeout)


def get_json(path):
    return json.loads(fetch(path))


def send_json(path, payload, method, timeout=60):
    """POST or PUT a JSON body with the PAT attached.

    Returns the decoded response, or None on an empty body: Jira answers a
    transition or a field edit with 204 No Content.

    Writes are deliberately kept in this one function so there is a single place
    to audit what can change a ticket or a page.
    """
    body = json.dumps(payload).encode('utf-8')
    raw = _request(absolute(path), 'application/json', data=body, method=method,
                   timeout=timeout)
    return json.loads(raw) if raw.strip() else None
