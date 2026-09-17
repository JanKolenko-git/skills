"""Shared HTTP/auth helpers for the confluence skill.

Targets Confluence Server / Data Center: the /rest/api/content endpoints, storage
format XHTML, and a personal access token sent as a Bearer credential. Confluence
Cloud lives under /wiki with different auth, and will not work here.

Reads CONFLUENCE_URL and CONFLUENCE_PERSONAL_TOKEN from the environment.
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
    url = os.environ.get('CONFLUENCE_URL', '')
    if not url:
        die('CONFLUENCE_URL is not set. Point it at your Confluence Data Center '
            'instance, e.g. export CONFLUENCE_URL=https://confluence.example.com '
            '(in ~/.zshenv).')
    return url.rstrip('/')


def _token():
    token = os.environ.get('CONFLUENCE_PERSONAL_TOKEN', '')
    if not token:
        die('CONFLUENCE_PERSONAL_TOKEN is not set. In Confluence, open the profile '
            'menu -> Personal Access Tokens, create one, then export it (e.g. in '
            '~/.zshenv). A Jira token will not work here — the tokens are per-product.')
    return token


def _ssl_context():
    # Verification stays on by default. Set CONFLUENCE_INSECURE_TLS=1 only if a
    # TLS-inspecting corporate proxy breaks an otherwise valid chain.
    if os.environ.get('CONFLUENCE_INSECURE_TLS') == '1':
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
        die('redirected to the Microsoft SSO login page instead of reaching the '
            'Confluence API, so the request never arrived. This is a network problem, '
            'not a token problem — connect to the corporate network or VPN and retry. '
            'If it persists while on VPN, CONFLUENCE_PERSONAL_TOKEN may have been '
            'revoked; create a fresh one in Confluence.', EXIT_HTTP)
    # Only when JSON was asked for: an attachment may legitimately be HTML.
    if 'json' in accept and body[:512].lstrip()[:1] == b'<':
        die(f'expected JSON from {final_url} but got an HTML page — most likely a login '
            f'or captive portal in front of Confluence rather than Confluence itself.',
            EXIT_HTTP)


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
            die('HTTP 401 — CONFLUENCE_PERSONAL_TOKEN was rejected. It has probably '
                'expired; create a fresh one in Confluence.', EXIT_HTTP)
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


def send_json(path, payload, method='PUT', timeout=60):
    """PUT/POST a JSON body with the PAT attached. Returns the decoded response.

    Writes are deliberately kept in this one function so there is a single place
    to audit what can change a page.

    A 409 means the page's version moved under us — someone edited it between our
    read and this write. That is reported, never retried blind: retrying with a
    bumped number would overwrite their edit.
    """
    if not (path.startswith('http://') or path.startswith('https://')):
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
            return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode('utf-8', 'replace')[:400]
        except Exception:
            detail = ''
        if e.code == 401:
            die('HTTP 401 — CONFLUENCE_PERSONAL_TOKEN was rejected. It has probably '
                'expired; create a fresh one in Confluence.', EXIT_HTTP)
        if e.code == 403:
            die(f'HTTP 403 — the token is valid but this account cannot edit this '
                f'page. {detail}', EXIT_FORBIDDEN)
        if e.code == 404:
            die(f'HTTP 404 — not found: {path}', EXIT_NOTFOUND)
        if e.code == 409:
            die('HTTP 409 — the page changed since it was read, so writing now would '
                'overwrite someone else\'s edit. Re-read the page and apply the update '
                'again.', EXIT_HTTP)
        die(f'HTTP {e.code} — {detail}', EXIT_HTTP)
    except urllib.error.URLError as e:
        die(f'cannot reach {path} ({e.reason}). Is the host right, and are you on '
            f'the network or VPN it sits behind?', EXIT_NETWORK)


def parse_target(arg):
    """Turn a page URL or bare ID into ('id', <id>) or ('title', (space, title)).

    Handles the URL shapes Confluence hands out:
      /spaces/ENG/pages/1778320229/Some+Title
      /pages/viewpage.action?pageId=1778320229
      /display/ENG/Some+Title
      1778320229
    """
    arg = arg.strip()
    if re.fullmatch(r'\d+', arg):
        return ('id', arg)

    parsed = urllib.parse.urlparse(arg if '://' in arg else f'https://{arg}')
    query = urllib.parse.parse_qs(parsed.query)

    if 'pageId' in query:
        return ('id', query['pageId'][0])

    parts = [p for p in parsed.path.split('/') if p]

    for i, part in enumerate(parts):
        if part == 'pages' and i + 1 < len(parts) and re.fullmatch(r'\d+', parts[i + 1]):
            return ('id', parts[i + 1])

    if 'display' in parts:
        i = parts.index('display')
        if len(parts) >= i + 3:
            space = urllib.parse.unquote(parts[i + 1])
            title = urllib.parse.unquote_plus(parts[i + 2])
            return ('title', (space, title))

    die(f'could not work out a page from {arg!r}. Pass a page URL or a numeric page ID.')


def resolve_page_id(arg):
    """Resolve any accepted target to a numeric page ID."""
    kind, value = parse_target(arg)
    if kind == 'id':
        return value

    space, title = value
    url = (f'/rest/api/content?spaceKey={urllib.parse.quote(space)}'
           f'&title={urllib.parse.quote(title)}&limit=1')
    results = get_json(url).get('results', [])
    if not results:
        die(f'no page titled {title!r} in space {space}.', EXIT_NOTFOUND)
    return results[0]['id']


def page_url(page):
    """Absolute browser URL for a content object from the REST API."""
    webui = ((page.get('_links') or {}).get('webui')) or ''
    return f'{base_url()}{webui}' if webui else f'{base_url()}/pages/viewpage.action?pageId={page.get("id")}'
