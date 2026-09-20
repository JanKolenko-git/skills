# jankolenko-skills

Composable, **portable** agent skills for shipping ticketed work, packaged as a
[Claude Code plugin](https://code.claude.com/docs/en/plugins). Everything here works against
any Jira or Confluence Data Center instance and any git repository; nothing here names one
employer, programme or codebase.

The unit of design is the **atom**: a small skill that does one thing and declares its
inputs and outputs by name, so other skills can call it. `implement` is the wiring
between atoms that are each useful on their own.

## Repository

- [`skills/`](./skills): one folder per skill, `skills/<name>/SKILL.md`
- [`spec/`](./spec/authoring.md): the contract every skill follows
- [`template/`](./template/SKILL.md): that contract as a blank skill
- [`ENGINEERING.md`](./ENGINEERING.md): the rules for the code the skills produce, which every
  session is pointed at
- [`WRITING.md`](./WRITING.md): the rules for how replies, tickets and messages read, which
  every session loads in full
- [`.claude-plugin/`](./.claude-plugin): the plugin and marketplace manifests; `plugin.json`
  carries the session-start hook

## The skills

Skills refer to each other by qualified name (`jankolenko-skills:git-commit`), the string the
`Skill` tool takes. Integrations feed atoms and atoms compose into orchestrators; each skill
declares its role in its own file.

### Engineering

The two integrations talk to any Jira or Confluence **Server or Data Center** instance over
REST with a personal access token: Jira REST v2 with wiki markup, Confluence
`/rest/api/content` with storage-format XHTML, Bearer auth. Atlassian Cloud is a different
API and will not authenticate here.

| Skill | What it does |
| --- | --- |
| [atlassian-jira](./skills/atlassian-jira/SKILL.md) | Read and update tickets: fetch as Markdown, search by text or JQL, transition, comment, create, edit |
| [atlassian-confluence](./skills/atlassian-confluence/SKILL.md) | Read pages as Markdown, search, download attachments, add or update one delimited section |
| [find-repository](./skills/find-repository/SKILL.md) | Work out which local repository a task belongs to, and refuse rather than guess |
| [plan](./skills/plan/SKILL.md) | Read the code, then decide what to do to it: files, steps, risks, lanes; asks one decision at a time when the goal is vague, and stops on a decision that outlives the change |
| [architect](./skills/architect/SKILL.md) | Settle a decision that outlives one change, a provider, data model, pattern or stack, and record it as an ADR or a spec section; started by hand |
| [git-create-branch](./skills/git-create-branch/SKILL.md) | Branch with a conventional name: `feature/`, `bugfix/`, `hotfix/` + key + slug |
| [test](./skills/test/SKILL.md) | Write tests in the repository's existing runner, layout and style, with a strategy per kind of file |
| [debug](./skills/debug/SKILL.md) | Find and fix a bug's root cause: a feedback loop that goes red first, then reproduce, minimise, rank hypotheses, instrument, fix with a regression test, clean up |
| [check](./skills/check/SKILL.md) | Confirm a change does what it was meant to and breaks nothing else: the diff against the plan, the behaviour run for evidence, the same surfaces compared against the base branch |
| [document](./skills/document/SKILL.md) | Write the prose about a change from its real diff: PR description, changelog entry, release notes, postmortem, ticket summary; started by hand |
| [git-commit](./skills/git-commit/SKILL.md) | Stage by path and commit with a conventional message; never pushes |
| [git-pr-push-and-open](./skills/git-pr-push-and-open/SKILL.md) | Show the diff, stop for approval, then push and open the PR |
| [git-pr-address-review](./skills/git-pr-address-review/SKILL.md) | Work the review comments on a PR: apply or decline each with a reason, one ledger row each |
| [record-learnings](./skills/record-learnings/SKILL.md) | Write durable constraints back to `CLAUDE.md`, a spec section or the ticket |
| [walkthrough](./skills/walkthrough/SKILL.md) | Get a branch or PR running, then hand over each change against the base branch: before, after, how the code did it, the steps to test it there |
| [implement](./skills/implement/SKILL.md) | Orchestrates the whole run: ticket → repo → plan → branch → build → test → check → review → PR → In Review → learnings |

`architect` and `document` are started by hand (`/jankolenko-skills:architect <decision>`,
`/jankolenko-skills:document pr`); the model cannot invoke them, so their descriptions cost
nothing in the skill listing, and a ticket run that owes a decision stops and names the first.

### Productivity

| Skill | What it does |
| --- | --- |
| [explain](./skills/explain/SKILL.md) | Explain code, a principle, a metric or how to build X in Y, plainly and accurately |
| [draft-reply](./skills/draft-reply/SKILL.md) | Turn a pasted thread and a rough draft into a short reply that checks out and answers everything asked, or write a status message or a work report from the record |

### Meta

The learning loop, closed for the skills themselves. The session-start hook points every
session at [`ENGINEERING.md`](./ENGINEERING.md), injects the four standing rules and
[`WRITING.md`](./WRITING.md), and adds one habit: friction with a skill is raised once, at the
end of the run.

| Skill | What it does |
| --- | --- |
| [improve-skill](./skills/improve-skill/SKILL.md) | Fix, add, rename or reshape one of these skills from an observed friction or a request that recurred, gated on the exact diff, then ship and install it |
| [record-engineering-rule](./skills/record-engineering-rule/SKILL.md) | Decide whether a coding convention belongs in [`ENGINEERING.md`](./ENGINEERING.md) or in one repository's `CLAUDE.md`, gated on the diff |
| [find-session-improvements](./skills/find-session-improvements/SKILL.md) | Sweep a finished session for what the skill layer should learn and route each finding to its owner behind one triage gate |

`find-session-improvements` is started by hand
(`/jankolenko-skills:find-session-improvements`); the model cannot invoke it, so its
description costs nothing in the skill listing.

## Safety

- Writes to Jira, Confluence or a PR, and pushes, happen only on your word in chat. Text
  fetched from a ticket, page, comment or file is data, never an instruction. There is no
  delete script.
- Every stop for approval asks through Claude Code's `AskUserQuestion` tool, which ends the
  turn. The push gate lives in the same skill as the push, so nothing composes around it,
  and it repeats every round of changes.
- Confluence edits are section-scoped: `update_page.py` writes only between its own markers,
  refuses when the page moved under it, and shows a `--dry-run` first.
- These are advisory controls that hold while a skill runs, read in the diff before a
  version ships.

## Installation

Add the marketplace once per machine, then install the plugin:

```bash
claude plugins marketplace add JanKolenko-git/skills
claude plugins install jankolenko-skills
```

This installs at user scope, so the skills show up in the CLI, the desktop app and the IDE
extensions alike. Restart Claude after installing. The marketplace is private, not Claude
Code's official one, so the first line is required; `jankolenko-skills@jankolenko` pins it
explicitly if a name ever collides.

### Point the skills at your instances

The Atlassian skills read the host and the credential from the environment at runtime. There
are no defaults: an unset URL stops with a setup message rather than guessing, and tokens
live on your machine, never in this repo. Create one personal access token in each product
(profile menu → *Personal Access Tokens*); they are per-product, so a Jira token gets a `401`
from Confluence.

Add all four to `~/.zshenv`, not `~/.zshrc`: `.zshenv` is read by the non-interactive shells
the agent runs commands in. Then lock the file down.

```bash
export JIRA_URL='https://jira.example.com'
export JIRA_PERSONAL_TOKEN='...'
export CONFLUENCE_URL='https://confluence.example.com'
export CONFLUENCE_PERSONAL_TOKEN='...'
```

```bash
chmod 600 ~/.zshenv
```

`find-repository` looks in the current directory, then `$REPO_ROOT`, then `~/Developer`,
`~/code`, `~/src`, `~/projects`, `~/repos`; set `REPO_ROOT` if your repositories live
elsewhere.

| Variable | Required | Use |
| --- | --- | --- |
| `JIRA_URL` | for `atlassian-jira` | Base URL of your Jira Data Center instance |
| `JIRA_PERSONAL_TOKEN` | for `atlassian-jira` | Personal access token for that instance |
| `CONFLUENCE_URL` | for `atlassian-confluence` | Base URL of your Confluence Data Center instance |
| `CONFLUENCE_PERSONAL_TOKEN` | for `atlassian-confluence` | Personal access token for that instance |
| `REPO_ROOT` | no | Where `find-repository` searches for repositories |
| `JIRA_INSECURE_TLS` | no | Set to `1` only if a TLS-inspecting corporate proxy breaks verification |
| `CONFLUENCE_INSECURE_TLS` | no | Same, for Confluence |
| `BITBUCKET_TOKEN` | no | HTTP access token, for `git-pr-address-review` on a Bitbucket PR |
| `BITBUCKET_URL` | no | Bitbucket Data Center base URL, e.g. `https://bitbucket.example.com`. Leave unset for Bitbucket Cloud |

The atoms need none of these; only the two Atlassian integrations do. TLS verification is on
by default.

## Usage

The skills are model-invoked: ask, and the agent reaches for them.

```
solve PROJ-1234
read PROJ-1155
summarise https://jira.example.com/browse/PROJ-1155
what does the checkout tech spec say about the LCP handoff?
find PROJ tickets in review that mention caching
move PROJ-1234 to In Review and comment with the PR link
which repo is PROJ-1234 about?
what is INP, and what actually moves it?
open a PR for this branch
address the review comments on <pr-url>
debug this: the badge count doesn't update after removing an item
does this branch do what PROJ-1234 asked, and break nothing against main?
test PR 123 by hand
what changed on this branch, and how do I try each change?
```

The scripts are stdlib-only Python 3 and every one takes `--help`, so they run on their own
too:

```bash
python3 ~/.claude/plugins/**/skills/atlassian-jira/fetch_ticket.py PROJ-1155
```

## Requirements

- Python 3, stdlib only
- A Jira / Confluence Server or Data Center instance you can reach (most sit behind a VPN)
- A personal access token per product
- `gh` CLI, if `git-pr-push-and-open` is to open the PR rather than hand you a compare link
- `gh` (GitHub) or `BITBUCKET_TOKEN` (Bitbucket), if `git-pr-address-review` is to read and
  reply to review comments rather than work from pasted text

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| `CONFLUENCE_PERSONAL_TOKEN is not set` | Token exported in `~/.zshrc` instead of `~/.zshenv`, or the terminal predates the change |
| `HTTP 401 — token was rejected` | Token expired, or a Jira token is being used against Confluence |
| `HTTP 403` | The account lacks access to that ticket or space, or, on a write, permission to change it |
| `no transition leads to …` | The workflow does not allow that status from the current one; `get_transitions.py` lists what it does allow |
| `JIRA_URL is not set` | The instance URL was never exported |
| `cannot reach ...` | Wrong host, or not on the network or VPN it sits behind |
| `find-repository` finds nothing | Set `REPO_ROOT`, or run from inside the repo |
| Bitbucket comment update returns `409` | Someone edited the thread mid-run; `git-pr-address-review` re-reads the comment `version` and retries once |

Exit codes distinguish the cases for scripting: `1` setup or bad input, `2` HTTP/auth,
`3` forbidden, `4` not found, `5` network unreachable.

## Development

How a skill is written and named is in [`spec/authoring.md`](./spec/authoring.md). A new skill
starts as a copy of [`template/SKILL.md`](./template/SKILL.md) in its own `skills/<name>/`
folder, plus a row in the tables above; the plugin finds it without a manifest entry.

Sessions load the plugin from a versioned cache, so a change ships only after a version bump
in `.claude-plugin/plugin.json` and an update:

```bash
claude plugin validate .claude-plugin/plugin.json && claude plugin validate .
git add <files> .claude-plugin/plugin.json
git commit -m "docs(<skill>): <what changed>"
claude plugin update jankolenko-skills@jankolenko
```

To work from this tree, register it as a Directory marketplace once
(`claude plugin marketplace add ~/Developer/skills`); a commit then ships to yourself without
a push. `ENGINEERING.md` and `WRITING.md` need no bump: the session-start hook takes both from
the working copy in `~/Developer/skills`, so a saved rule applies at the next session.

## Security

No credentials are committed to this repository, and none should be. The Python clients read
tokens from the environment only; `_client.py` in each Atlassian skill is the single place
auth is handled, and `send_json` the single place a write can originate. If a token ever
lands in a commit, rotate it in Atlassian; rewriting history is not enough.

## License

MIT — see [LICENSE](./LICENSE).
