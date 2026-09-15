# Confluence writes

Read when `mode` is `update_section`, after the gate in `SKILL.md` → Writes. `<skill-dir>`
below is the folder holding `SKILL.md`, the one the skill printed as `${CLAUDE_SKILL_DIR}`.

## Storage format, not Markdown

Page bodies are Confluence storage format: XHTML with `<ac:…>` macro elements. Markdown
handed to `update_page.py` is written verbatim and renders as literal asterisks, so generate
`<h2>`, `<p>`, `<ul>`, `<table>` directly. `fetch_page.py --format storage` shows the
surrounding markup to match.

## Updating a section

```bash
python3 <skill-dir>/update_page.py <page-url-or-id> \
  --marker ticket-report:PROJ-4821 \
  --heading "Verification — PROJ-4821" \
  --body-file "$TMPDIR/report.xhtml" --dry-run
```

The script wraps the content in comment markers and writes only between them:

```
<!-- ticket-report:PROJ-4821 START -->  …content…  <!-- … END -->
```

The first run appends the block; later runs replace its contents in place, so nothing a
colleague wrote elsewhere on the page is touched and re-running does not stack copies.
Always `--dry-run` first and show the user what would change: Confluence has no append
primitive, every update PUTs the whole body, and the blast radius of a mistake is the entire
page.

## What the script refuses

Three cases exit non-zero rather than guess. Do not work around any of them.

| Situation | Why it stops |
| --- | --- |
| `409` from the API | The page changed between read and write; writing now would erase that edit. Re-read and redo, never retry with a bumped version number |
| Only one of the two markers present | Section boundaries are unclear; a write could swallow unrelated content |
| No markers, but the heading already exists | An editor session probably stripped the comments; appending would duplicate the section |

## A refused write

Not fatal to a larger flow: report the message and carry on. A `403` means the account
cannot edit that page; say so rather than trying another route.
