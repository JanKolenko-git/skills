# Plan: one command per Atlassian product

A proposal, not a change. Edit only on an explicit go, under the gate of
`jankolenko-skills:improve-skill`. Written 2026-09-28 from the working copy at `3b64760`.
This file sits on the branch for review only; the shipping commit deletes it, because a plan
file stays outside the repository (`spec/authoring.md`, Changing the skill layer).

## What it changes

The 17 Python files under `skills/engineering/atlassian-jira/` and
`skills/engineering/atlassian-confluence/` become 5: one command per product with
subcommands, one HTTP client per product that is identical to the other except for its
product name, and the Confluence HTML converter. The Jira wiki-markup converter, the
attachment lister and every duplicated helper go. Three small behaviours improve: the
Confluence dry run shows the section it would write, a page fetch requests one body format,
and a page fetch lists each attachment with its download URL.

The `## Inputs` and `## Output` tables of both `SKILL.md` files do not change, so no caller
changes. Every guarantee the README makes stays true by construction: auth in one file,
`send_json` the one function a write can originate from, no delete path, the token never
printed, and the section-scoped Confluence write with its three refusals.

| | Files | Lines |
| --- | --- | --- |
| Measured now | 17 | 1,707 |
| Estimated after | 5 | about 1,300 |
| Estimated after, if open question 1 deletes the HTML converter | 4 | about 1,040 |

## The record

The question this answers, asked in chat on 2026-09-28:

> Do I need all these `py` scripts in [...]/atlassian-jira and [...]/atlassian-confluence
> or can it be simplified with AI instructions?

The lessons a failure bought, as the scripts' own comments record them. Each survives the
change, in the place named:

| Lesson | Recorded in | Lives on in |
| --- | --- | --- |
| A corporate SSO edge answers every REST call with a login page at HTTP 200, which surfaces as a JSON parse error far from the cause | `_client.py`, `_reject_sso_page` | `_client.py`, unchanged |
| A 401 is an expired or wrong-product token; a 403 is a permission, never retried by another route | `_client.py` | `_client.py`, unchanged |
| Confluence has no append primitive; every update PUTs the whole body, and a 409 means the page moved under the read | `update_page.py`, `_client.py` | `confluence.py update-section` |
| Markers stripped by a human edit would make an append duplicate the section | `update_page.py`, `splice` | `confluence.py update-section` |
| A transition id comes from the workflow, never guessed; an ambiguous name is refused with the list | `transition_issue.py` | `jira.py transition` |
| The Jira-issue macro leaves "Getting issue details... STATUS" in the view body, which reads as a status | `_markdown.py` | `_markdown.py`, unchanged |
| Jira pads `{{monospace}}` with `{}` | `_markup.py` | one sentence in the Jira `SKILL.md`, Step 1 |

Measured on the working copy:

| Measure | Value |
| --- | --- |
| Python files, lines | 17, 1,707 (Jira 10 files, 871 lines; Confluence 7 files, 836 lines) |
| Markdown files, lines | 4, 315 |
| The two `_client.py` | 182 and 210 lines. The HTTP core (`die`, `base_url`, `_token`, `_reject_sso_page`, `fetch`, `get_json`, `send_json`) is the same code; they differ in wording, a 409 branch, and the URL parsing each product needs |
| `download_attachment.py` | identical in both skills except docstrings |
| `_size()` | defined three times |
| Files with their own `argparse` main | 13 |
| Callers outside the two folders that run a script | 0. `implement`, `record-learnings`, `architect`, `draft-reply` and `walkthrough` invoke the skill by name and read `ticket.*` and `page.*` |
| Doc lines that name a script | 23 in the two skills, 4 in `README.md` |
| Tests or evals | none; the evals went in `5ef8795` |
| `--help` with no environment set | every one of the 13 entry scripts, on Python 3.11 |

## Verdict per file

| File | Lines | Becomes |
| --- | --- | --- |
| `atlassian-jira/_client.py` | 182 | Kept, HTTP only. `parse_key` and `browse_url` move to `jira.py` |
| `atlassian-jira/_markup.py` | 123 | Deleted. The model reads wiki markup as it is |
| `atlassian-jira/fetch_ticket.py` | 161 | `jira.py fetch` |
| `atlassian-jira/search_issues.py` | 61 | `jira.py search` |
| `atlassian-jira/get_transitions.py` | 39 | `jira.py transitions` |
| `atlassian-jira/transition_issue.py` | 86 | `jira.py transition` |
| `atlassian-jira/add_comment.py` | 43 | `jira.py comment` |
| `atlassian-jira/create_issue.py` | 66 | `jira.py create` |
| `atlassian-jira/edit_issue.py` | 77 | `jira.py edit` |
| `atlassian-jira/download_attachment.py` | 33 | `jira.py download` |
| `atlassian-confluence/_client.py` | 210 | Kept, HTTP only. `parse_target`, `resolve_page_id` and `page_url` move to `confluence.py` |
| `atlassian-confluence/_markdown.py` | 261 | Kept as it is (open question 1) |
| `atlassian-confluence/fetch_page.py` | 106 | `confluence.py fetch`, with attachment download URLs and one body format per request |
| `atlassian-confluence/search_pages.py` | 51 | `confluence.py search` |
| `atlassian-confluence/list_attachments.py` | 48 | Deleted. The fetch already receives each attachment's `_links.download` and only had to print it |
| `atlassian-confluence/download_attachment.py` | 33 | `confluence.py download` |
| `atlassian-confluence/update_page.py` | 127 | `confluence.py update-section`, with a dry run that prints the section |

## Target layout

```
skills/engineering/atlassian-jira/
  SKILL.md
  reference/writes.md
  jira.py          fetch | search | transitions | transition | comment | create | edit | download
  _client.py       HTTP, auth, errors, exit codes; PRODUCT = 'Jira' is the only line that differs

skills/engineering/atlassian-confluence/
  SKILL.md
  reference/writes.md
  confluence.py    fetch | search | download | update-section
  _client.py       PRODUCT = 'Confluence'
  _markdown.py     HTML to Markdown, unchanged
```

The contract of the two commands:

1. `python3 ${CLAUDE_SKILL_DIR}/jira.py <subcommand> ...`, and the same for `confluence.py`.
   `--help` answers at both levels with no environment set.
2. A read prints Markdown on stdout. A write prints one confirmation line ending in the URL.
   An error goes to stderr with the existing exit codes: `1` setup or bad input, `2` HTTP or
   auth, `3` forbidden, `4` not found, `5` network unreachable.
3. Every write goes through `send_json` in `_client.py`, with `method=` passed explicitly at
   each call. There is no delete subcommand.
4. `_client.py` derives `<PRODUCT>_URL` and `<PRODUCT>_PERSONAL_TOKEN` from one `PRODUCT`
   constant, never prints the token, and never takes it as an argument.
5. The two `_client.py` files are identical except the `PRODUCT` line. A skill never imports
   across folders (`spec/authoring.md`, Layout), so the copy is deliberate, and `diff` is what
   stops the copies drifting:

   ```bash
   diff <(grep -v '^PRODUCT = ' skills/engineering/atlassian-jira/_client.py) \
        <(grep -v '^PRODUCT = ' skills/engineering/atlassian-confluence/_client.py)
   ```

## The edits, priced

| # | Edit | Buys | Verdict |
| --- | --- | --- | --- |
| 1 | Fold the eight Jira scripts into `jira.py` with subparsers | One `--help` for the product; 8 mains, 8 import blocks and 8 docstrings become one; one file to read | do |
| 2 | Fold the five Confluence scripts into `confluence.py`; `fetch` prints each attachment's download URL; `list_attachments.py` goes | The same, minus 48 lines and one round trip per page with attachments | do |
| 3 | Reduce both clients to HTTP, auth and errors with one `PRODUCT` constant; move URL parsing into the command that needs it | A fix to the SSO or 401 handling lands in both, provably | do |
| 4 | Delete `_markup.py`; `jira.py fetch` prints the description and comments as wiki markup | 123 untested regex lines gone; wiki markup is as compact as Markdown and the model reads it; one sentence in `SKILL.md` keeps the `{}` lesson | do |
| 5 | `update-section --dry-run` prints the section it would write, and the current one when it replaces | The gate block asks for the exact artefact on screen; today the dry run prints character counts | do, about 15 lines |
| 6 | `confluence.py fetch` requests only the body format asked for, the other only when the first is empty | Halves the response on a large page (estimate); today both bodies come back every time | do |
| 7 | Rename in the docs: 23 lines in the two skills, 4 in `README.md` | The docs match the tree | do |
| 8 | Delete `_markdown.py` and print the view HTML | 261 untested lines gone | open question 1 |

Considered and dropped, with the price that dropped it:

| Option | Would remove | Dropped because |
| --- | --- | --- |
| Reads through `curl`, described in a reference file; Python only for the writes | About 1,100 lines, adding about 90 lines of Markdown | Every read pays raw JSON or HTML (2 to 4 times the Markdown on a page, estimate); JQL quoting and URL-encoding vary per run; a `-v` prints the bearer header into the transcript; the exit codes go; two mechanisms instead of one. The fetch is the plugin's most repeated call: `implement` invokes the Jira skill three times per ticket. This was the recommendation in chat before pricing; the pricing moved it |
| One shared client at the plugin root, reached through `${CLAUDE_PLUGIN_ROOT}` | About 135 lines | The spec keeps a skill inside its own folder; the `diff` check in the contract gives the same guarantee for one grep |
| An MCP server in place of the scripts | All 1,707 lines | The Atlassian Rovo server is Cloud-only. The community `mcp-atlassian` supports Data Center but adds a runtime to install per machine and has no section-scoped write, so `update-section` would be rebuilt anyway |
| Keep as is | 0 | 13 mains, 3 `_size`, and two clients that already disagree on wording and a 409 branch |

## Contract and example output

Jira `SKILL.md`, `## Scripts`, after:

```bash
python3 ${CLAUDE_SKILL_DIR}/jira.py fetch <key-or-url> [--comments 5 | --no-comments | --json]
python3 ${CLAUDE_SKILL_DIR}/jira.py search "checkout timeout" --project PROJ --limit 20
python3 ${CLAUDE_SKILL_DIR}/jira.py search 'project = PROJ AND status = "In Review"'
python3 ${CLAUDE_SKILL_DIR}/jira.py transitions <key-or-url>
python3 ${CLAUDE_SKILL_DIR}/jira.py download <content-url> "$TMPDIR/screenshot.png"
```

Jira Step 1, in place of "renders wiki markup to Markdown": "`fetch` prints the description
and comments as Jira wiki markup. Render them as Markdown in the report. Ignore the `{}` Jira
pads `{{monospace}}` with." `ticket.description` stays "as Markdown": the field is what the
skill reports, not what the script prints.

Jira `reference/writes.md`, the four writes:

```bash
python3 <skill-dir>/jira.py transition <key-or-url> "In Review"
python3 <skill-dir>/jira.py comment <key-or-url> "<text>"          # or --stdin < body.txt
python3 <skill-dir>/jira.py create --project PROJ --type Bug --summary "..." --description "..."
python3 <skill-dir>/jira.py edit <key-or-url> --assignee jsmith --add-label needs-qa
```

Confluence `SKILL.md`, `## Scripts`, after:

```bash
python3 ${CLAUDE_SKILL_DIR}/confluence.py fetch <page-url-or-id> [--json | --format storage]
python3 ${CLAUDE_SKILL_DIR}/confluence.py search "checkout tech spec" --space ENG --limit 10
python3 ${CLAUDE_SKILL_DIR}/confluence.py download <download-url> "$TMPDIR/diagram.png"
```

Confluence `reference/writes.md`, the write:

```bash
python3 <skill-dir>/confluence.py update-section <page-url-or-id> \
  --marker ticket-report:PROJ-4821 --heading "Verification: PROJ-4821" \
  --body-file "$TMPDIR/report.xhtml" --dry-run
```

The dry run, after. Today it prints `body: 41230 chars -> 41377 chars`:

```
DRY RUN: would update 'ticket-report:PROJ-4821' on "Checkout tech spec" (1778320229, v12 -> v13)
--- current section
<!-- ticket-report:PROJ-4821 START -->
<h2>Verification: PROJ-4821</h2><p>Pending.</p>
<!-- ticket-report:PROJ-4821 END -->
+++ new section
<!-- ticket-report:PROJ-4821 START -->
<h2>Verification: PROJ-4821</h2><p>Verified on staging, 3 of 3 criteria.</p>
<!-- ticket-report:PROJ-4821 END -->
https://confluence.example.com/pages/viewpage.action?pageId=1778320229
```

A page fetch header, after, with the attachment lines that replace the lister:

```
- **Attachments (2):**
  - checkout-flow.png (image/png, 212 KB): https://confluence.example.com/download/attachments/1778320229/checkout-flow.png
  - timings.csv (text/csv, 9 KB): https://confluence.example.com/download/attachments/1778320229/timings.csv
```

`README.md` changes four lines: the Safety bullet names `confluence.py update-section`, the
Usage example runs `jira.py fetch PROJ-1155`, the Troubleshooting row names
`jira.py transitions`, and the Security paragraph stays as written, since `_client.py` and
`send_json` keep their roles.

## Sequence

One commit per step, each shippable alone. Step 1 is a refactor with no behaviour change;
steps 2 to 4 each change one behaviour.

| Step | Commit | Done when |
| --- | --- | --- |
| 1 | `refactor(atlassian): one command per product, clients identical` (edits 1 to 4 and 7) | `python3 -m py_compile` on the 5 files passes; every subcommand answers `--help` with no environment set; the client `diff` above prints nothing; `grep -rn '\.py' README.md skills/` names only `jira.py`, `confluence.py`, `_client.py` and `_markdown.py`; `claude plugin validate .` passes; `claude --plugin-dir . plugin details jankolenko-skills` lists both skills |
| 2 | `feat(atlassian-confluence): dry run prints the section it would write` (edit 5) | a `--dry-run` against a test page prints the current and the new section, and the page version does not move |
| 3 | `perf(atlassian-confluence): fetch one body format` (edit 6) | a fetch of a page whose view and storage bodies are both non-empty prints the same Markdown as before |
| 4 | `feat(atlassian-confluence): fetch lists attachment download URLs` (edit 2, second half) | a page with an attachment prints its URL, and `download` with that URL writes the file |
| 5 | Ship: bump `8.4.3` to `8.5.0`, validate, commit, `claude plugin update jankolenko-skills@jankolenko`, `claude plugin list`; delete this file in the same commit | `claude plugin list` shows `8.5.0` |
| 6 | Three real runs on the new commands (`read PROJ-…`, `implement`), then settle open question 1 | three runs, the last needing no fix |

What a cloud session can verify: compile, `--help`, the client `diff` and the doc `grep`.
What needs your machine: anything against an instance (VPN and a PAT), the plugin commands,
and steps 2 to 6. Nothing in this plan was run against Jira or Confluence. The 13 current
scripts were compiled and their `--help` run on Python 3.11 here.

## Open questions

Recommended answer first.

1. `_markdown.py`: keep it (the view HTML of a large page is 2 to 4 times the Markdown,
   estimate, and a run reads up to three pages; revisit after step 6), or delete it now (261
   untested lines; the model reads HTML).
2. The Jira description: print it as wiki markup (the model reads it; the one `{}` lesson
   moves to `SKILL.md`), or keep converting it (keep `_markup.py`, 123 lines).
3. Version: minor, `8.5.0` (a command surface a person may have scripted is renamed; the
   skill contract is not), or patch.
4. This file: deleted in the shipping commit (the spec keeps plan files outside the
   repository), or kept in a `plans/` folder with the spec amended.

## Not in this plan

Jira or Confluence Cloud, a different API and auth. A wording pass on either `SKILL.md`
beyond the lines the renames touch. A test or eval harness for the plugin. Replacing the
scripts with `mcp-atlassian`.
