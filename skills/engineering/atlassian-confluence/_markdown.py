"""Convert Confluence HTML to Markdown.

Handles both bodies the REST API can return: the rendered `view` HTML (default,
macros already expanded) and the raw `storage` XHTML (with `ac:`/`ri:` tags).

Pure stdlib on purpose — the skill must work with no pip installs.
"""
import re
from html.parser import HTMLParser

# Stands in for list indentation so the whitespace cleanup can't eat it.
INDENT = '\x00'

SKIP_TAGS = {'script', 'style', 'noscript', 'head'}
HEADINGS = {f'h{n}': n for n in range(1, 7)}
BLOCK_TAGS = {'p', 'div', 'section', 'article', 'header', 'footer', 'dl', 'dd', 'dt'}


def _flatten_cell(text):
    """Markdown table cells are single-line, so collapse and escape pipes."""
    text = re.sub(r'\s+', ' ', text.replace(INDENT, ' ')).strip()
    return text.replace('|', r'\|')


def _render_table(rows):
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        return ''
    width = max(len(r) for r in rows)
    rows = [r + [''] * (width - len(r)) for r in rows]
    lines = [
        '| ' + ' | '.join(rows[0]) + ' |',
        '| ' + ' | '.join(['---'] * width) + ' |',
    ]
    lines += ['| ' + ' | '.join(r) + ' |' for r in rows[1:]]
    return '\n'.join(lines)


def strip_macro_placeholders(text):
    """Drop placeholder text left by macros that resolve client-side.

    The Jira-issue macro is the common one: the `view` body ships
    "Getting issue details... STATUS", which reads as if the ticket's status
    were literally "STATUS".
    """
    return re.sub(r'\s*-?\s*Getting issue details\.\.\.\s*STATUS', '', text)


def _cleanup(text):
    # Normalise whitespace everywhere except inside fenced code blocks.
    parts = text.split('```')
    for i, part in enumerate(parts):
        if i % 2:
            continue
        part = re.sub(r'[ \t]+', ' ', part)
        part = re.sub(r' *\n *', '\n', part)
        part = strip_macro_placeholders(part)
        part = re.sub(r'\n{3,}', '\n\n', part)
        parts[i] = part
    text = '```'.join(parts).replace(INDENT, ' ')
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    return re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'


class _Converter(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_depth = 0
        self.pre_depth = 0
        self.lists = []      # ['ul'|'ol', item_count]
        self.tables = []     # {'rows': [...], 'row': [...], 'cell': [...] | None}
        self.links = []
        self.quotes = []     # indices into self.out where a blockquote opened
        self.fresh_li = False

    # -- output plumbing ---------------------------------------------------

    def _emit(self, text):
        if self.skip_depth or not text:
            return
        if self.tables and self.tables[-1]['cell'] is not None:
            self.tables[-1]['cell'].append(text)
        else:
            self.out.append(text)

    def _block(self):
        """Paragraph break, unless we just opened a list item."""
        if self.fresh_li:
            return
        self._emit('\n\n')

    # -- parser callbacks --------------------------------------------------

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return

        attrs = dict(attrs)

        if tag == 'br':
            self._emit('\n')
        elif tag in HEADINGS:
            self._block()
            self._emit('#' * HEADINGS[tag] + ' ')
        elif tag in BLOCK_TAGS:
            self._block()
        elif tag == 'hr':
            self._block()
            self._emit('---')
            self._block()
        elif tag in ('ul', 'ol'):
            if not self.lists:
                self._block()
            self.lists.append([tag, 0])
        elif tag == 'li':
            kind, count = self.lists[-1] if self.lists else ['ul', 0]
            if self.lists:
                self.lists[-1][1] += 1
                count = self.lists[-1][1]
            depth = max(0, len(self.lists) - 1)
            marker = f'{count}. ' if kind == 'ol' else '- '
            self._emit('\n' + INDENT * (depth * 2) + marker)
            self.fresh_li = True
        elif tag == 'a':
            href = attrs.get('href', '')
            self.links.append(href)
            if href:
                self._emit('[')
        elif tag in ('strong', 'b'):
            self._emit('**')
        elif tag in ('em', 'i', 'cite'):
            self._emit('*')
        elif tag in ('del', 's', 'strike'):
            self._emit('~~')
        elif tag == 'code' and not self.pre_depth:
            self._emit('`')
        elif tag in ('pre', 'ac:plain-text-body'):
            self._block()
            self._emit('```\n')
            self.pre_depth += 1
        elif tag == 'blockquote':
            self._block()
            # Remember where the quote starts so `>` can prefix every line of it
            # once we know the content — emitting `> ` up front strands it on its
            # own line whenever the first child is a block element.
            self.quotes.append(len(self.out))
        elif tag == 'table':
            self._block()
            self.tables.append({'rows': [], 'row': [], 'cell': None})
        elif tag == 'tr':
            if self.tables:
                self.tables[-1]['row'] = []
        elif tag in ('td', 'th'):
            if self.tables:
                self.tables[-1]['cell'] = []
        elif tag == 'img':
            src = attrs.get('src', '')
            alt = attrs.get('alt') or 'image'
            self._emit(f'![{alt}]({src})')
        # -- storage-format specifics
        elif tag == 'ri:attachment':
            name = attrs.get('ri:filename', '')
            if name:
                self._emit(f'![attachment]({name})')
        elif tag == 'ri:page':
            title = attrs.get('ri:content-title', '')
            if title:
                self._emit(f'[{title}]')
        elif tag == 'ac:structured-macro':
            name = attrs.get('ac:name', '')
            if name in ('info', 'note', 'warning', 'tip', 'panel'):
                self._block()
                self._emit(f'> **{name.upper()}** ')

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return

        if tag in HEADINGS or tag in BLOCK_TAGS:
            self._block()
        elif tag in ('ul', 'ol'):
            if self.lists:
                self.lists.pop()
            if not self.lists:
                self._block()
        elif tag == 'li':
            self.fresh_li = False
        elif tag == 'a':
            href = self.links.pop() if self.links else ''
            if href:
                self._emit(f']({href})')
        elif tag in ('strong', 'b'):
            self._emit('**')
        elif tag in ('em', 'i', 'cite'):
            self._emit('*')
        elif tag in ('del', 's', 'strike'):
            self._emit('~~')
        elif tag == 'code' and not self.pre_depth:
            self._emit('`')
        elif tag in ('pre', 'ac:plain-text-body'):
            self.pre_depth = max(0, self.pre_depth - 1)
            self._emit('\n```')
            self._block()
        elif tag == 'blockquote':
            start = self.quotes.pop() if self.quotes else None
            if start is not None and not (self.tables and self.tables[-1]['cell'] is not None):
                inner = strip_macro_placeholders(''.join(self.out[start:])).strip()
                del self.out[start:]
                if inner:
                    quoted = '\n'.join(
                        f'> {line}'.rstrip() for line in inner.split('\n'))
                    self.out.append(quoted)
            self._block()
        elif tag in ('td', 'th'):
            if self.tables and self.tables[-1]['cell'] is not None:
                table = self.tables[-1]
                table['row'].append(_flatten_cell(''.join(table['cell'])))
                table['cell'] = None
        elif tag == 'tr':
            if self.tables:
                table = self.tables[-1]
                if table['row']:
                    table['rows'].append(table['row'])
                table['row'] = []
        elif tag == 'table':
            if self.tables:
                table = self.tables.pop()
                self._emit(_render_table(table['rows']))
                self._block()

    def handle_data(self, data):
        if self.skip_depth or not data:
            return
        if self.pre_depth:
            self._emit(data)
            return
        text = re.sub(r'\s+', ' ', data)
        if not text.strip():
            self._emit(' ')
            return
        self._emit(text)
        self.fresh_li = False

    def unknown_decl(self, data):
        # Storage format wraps code-macro bodies in CDATA sections.
        if data.startswith('CDATA['):
            self._emit(data[len('CDATA['):])


def html_to_markdown(html):
    converter = _Converter()
    converter.feed(html or '')
    converter.close()
    return _cleanup(''.join(converter.out))
