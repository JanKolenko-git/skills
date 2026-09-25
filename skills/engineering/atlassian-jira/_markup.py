"""Convert Jira wiki markup (what Jira Data Center stores in text fields) to Markdown.

Descriptions and comments come back from `/rest/api/2` as wiki markup, not HTML and
not ADF. Rendering it makes tables, code blocks and lists readable instead of noise.

Pure stdlib on purpose — the skill must work with no pip installs.
"""
import re

_STASH = '\x00CODE{}\x00'


def _code_lang(params):
    """`{code:java}` -> java; `{code:title=X|language=java}` -> java."""
    lang = ''
    for part in (params or '').split('|'):
        part = part.strip()
        if not part:
            continue
        if '=' in part:
            key, value = part.split('=', 1)
            if key.strip() == 'language':
                lang = value.strip()
        else:
            lang = part
    return lang


def _inline(text):
    # {{mono}}. Jira often pads the delimiters with its empty-macro marker — the
    # real markup is `{{{}NAME{}}}` — and `{}` renders as nothing, so absorb it
    # here. Without this the non-greedy match anchors on the wrong brace pair and
    # emits `` `{}NAME{` `` followed by a stray `}`.
    text = re.sub(r'\{\{(?:\{\})?(.+?)(?:\{\})?\}\}', r'`\1`', text)
    text = re.sub(r'\[([^\]|]+)\|([^\]]+)\]', r'[\1](\2)', text)      # [text|url]
    text = re.sub(r'\[([a-zA-Z]+://[^\]]+)\]', r'<\1>', text)         # [url]
    text = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])', r'**\1**', text)
    text = re.sub(r'(?<![\w_])_([^_\n]+)_(?![\w_])', r'*\1*', text)
    text = re.sub(r'(?<![\w+])\+([^+\n]+)\+(?![\w+])', r'\1', text)   # +inserted+
    text = re.sub(r'\{color:[^}]*\}', '', text)
    text = text.replace('{color}', '')
    text = re.sub(r'\{(panel|quote)(:[^}]*)?\}', '', text)
    return text


def jira_to_markdown(text):
    if not text:
        return ''

    text = text.replace('\r\n', '\n')

    # Pull code/noformat bodies out first so nothing below rewrites their contents.
    stashed = []

    def stash(match):
        stashed.append(match.group(0))
        return _STASH.format(len(stashed) - 1)

    text = re.sub(r'\{code(?::[^}]*)?\}.*?\{code\}', stash, text, flags=re.S)
    text = re.sub(r'\{noformat\}.*?\{noformat\}', stash, text, flags=re.S)

    out = []
    header_done = False

    for raw in text.split('\n'):
        line = raw.rstrip()

        heading = re.match(r'^h([1-6])\.\s*(.*)$', line)
        if heading:
            out.append('#' * int(heading.group(1)) + ' ' + _inline(heading.group(2)))
            header_done = False
            continue

        if line.startswith('bq. '):
            out.append('> ' + _inline(line[4:]))
            header_done = False
            continue

        if re.fullmatch(r'-{4,}', line):
            out.append('---')
            header_done = False
            continue

        if line.startswith('|') and line.endswith('|') and len(line) > 1:
            if line.startswith('||'):
                cells = [_inline(c.strip()) for c in line.strip('|').split('||')]
                out.append('| ' + ' | '.join(cells) + ' |')
                out.append('| ' + ' | '.join(['---'] * len(cells)) + ' |')
                header_done = True
            else:
                cells = [_inline(c.strip()) for c in line.strip('|').split('|')]
                out.append('| ' + ' | '.join(cells) + ' |')
                if not header_done:
                    # Markdown needs a header row; promote the first one.
                    out.append('| ' + ' | '.join(['---'] * len(cells)) + ' |')
                    header_done = True
            continue

        header_done = False

        bullet = re.match(r'^([*#-]+)\s+(.*)$', line)
        if bullet:
            marks, body = bullet.groups()
            depth = len(marks) - 1
            marker = '1. ' if marks[-1] == '#' else '- '
            out.append('  ' * depth + marker + _inline(body))
            continue

        out.append(_inline(line))

    result = '\n'.join(out)

    for index, block in enumerate(stashed):
        code = re.match(r'\{code(?::([^}]*))?\}(.*?)\{code\}', block, re.S)
        if code:
            fence = f'```{_code_lang(code.group(1))}\n{code.group(2).strip()}\n```'
        else:
            plain = re.match(r'\{noformat\}(.*?)\{noformat\}', block, re.S)
            body = plain.group(1) if plain else block
            fence = f'```\n{body.strip()}\n```'
        result = result.replace(_STASH.format(index), fence)

    return re.sub(r'\n{3,}', '\n\n', result).strip()
