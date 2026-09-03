# jankolenko-skills

Composable, **portable** agent skills for shipping ticketed work, packaged as a
[Claude Code plugin](https://code.claude.com/docs/en/plugins).

Everything here works against any Jira/Confluence Data Center instance and any git repo —
nothing is bound to one employer or programme. The workflows that *are* bound to one live in
the companion [`jankolenko-projects`](https://github.com/JanKolenko-git/JanKolenko-Skills)
plugin, which depends on this one and not the other way round
([`adr/0004`](./.agents/adr/0004-two-repos.md)).

The unit of design here is the **atom**: a small skill that does one thing and declares its
inputs and outputs by name, so other skills can call it. `implement-ticket` is not a monolith —
it is the wiring between atoms that are each useful on their own.

## The skills

Skills sort into **buckets** by what they are about — `engineering/`, `productivity/` and
`meta/` here, `projects/` in the companion plugin — each at exactly
`skills/<bucket>/<skill-name>/SKILL.md`.

What a skill *does in a pipeline* is a separate axis, and it is the one that matters for
composing them. Every skill declares one of three **roles**, and read in that order they are
the dataflow: **integrations** feed **atoms**, atoms compose into **orchestrators**,
orchestrators specialise into the project workflows in the companion plugin, and `meta/`
watches all of it. Roles are
deliberately not folders — see
[`.agents/adr/0002-domain-buckets.md`](./.agents/adr/0002-domain-buckets.md).

Skills refer to each other by **qualified name** — `jankolenko-skills:git-commit`, never
bare `git-commit`. That is the string the `Skill` tool takes, so a step reads the same way it
runs, and it stays unambiguous now that the skills ship from two plugins of mine plus
whatever else you have installed.

### `engineering/` — everything that moves a diff toward a PR

#### Integrations — your Jira and Confluence

Talks to **any** Jira / Confluence **Server or Data Center** instance over the REST API with
a personal access token. You point `$JIRA_URL` and `$CONFLUENCE_URL` at your own hosts; the
token is what decides what you can see. No browser, no SSO dance, no MCP server to authorize.

> **Not Atlassian Cloud.** These speak Jira REST v2 with wiki markup and Confluence
> `/rest/api/content` with storage-format XHTML, authenticating with a Bearer PAT. Cloud is a
> different API (Jira v3 + ADF, Confluence under `/wiki`) with `email:api_token` Basic auth,
> and will not authenticate here.

| Skill | What it does |
| --- | --- |
| **[atlassian-jira](./skills/engineering/atlassian-jira/SKILL.md)** | Read and update tickets on your Jira instance — fetch as Markdown, search by text or JQL, transition status, comment, create and edit issues |
| **[atlassian-confluence](./skills/engineering/atlassian-confluence/SKILL.md)** | Read pages from your Confluence instance as Markdown, macros expanded and tables intact. Search, list and download attachments. Can add or update **one delimited section** on a page |

#### Atoms — reusable anywhere

Nothing instance-specific, nothing Jira-specific. They accept explicit inputs, and resolve a
ticket key on their own only if `atlassian-jira` happens to be installed.

| Skill | What it does |
| --- | --- |
| **[find-repository](./skills/engineering/find-repository/SKILL.md)** | Work out which local git repo a task belongs to — and refuse rather than guess |
| **[plan-change](./skills/engineering/plan-change/SKILL.md)** | Read the code, then decide what to do to it: files, steps, risks — and whether the work splits into independent lanes |
| **[clarify-goal](./skills/engineering/clarify-goal/SKILL.md)** | Turn a blocked plan into answered questions — facts get looked up, decisions go to you one at a time with a recommendation, answers fold back into the goal |
| **[git-create-branch](./skills/engineering/git-create-branch/SKILL.md)** | Branch with a conventional name: `feature/`, `bugfix/`, `hotfix/` + key + slug |
| **[write-tests](./skills/engineering/write-tests/SKILL.md)** | Write tests matching the repo's existing runner, layout and style |
| **[critique-plan](./skills/engineering/critique-plan/SKILL.md)** | Review the diff against the *plan*, not for bugs — what's missing, what's unplanned, whether it should exist |
| **[git-commit](./skills/engineering/git-commit/SKILL.md)** | Stage and commit with a conventional message. Local only — never pushes |
| **[git-pr-push-and-open](./skills/engineering/git-pr-push-and-open/SKILL.md)** | Show the diff, **stop for human approval**, then push and open the PR |
| **[git-pr-address-review](./skills/engineering/git-pr-address-review/SKILL.md)** | Work the review comments on a PR — apply the ones that earn a change, decline the rest with a reason, one ledger row each |
| **[record-learnings](./skills/engineering/record-learnings/SKILL.md)** | Write durable constraints back to `CLAUDE.md`, a spec section or the ticket — and drop everything that wasn't durable |

#### Orchestrators — workflows

| Skill | What it does |
| --- | --- |
| **[implement-ticket](./skills/engineering/implement-ticket/SKILL.md)** | Ticket → context → repo → plan → branch → implement → test → critique → review → PR → *In Review* → learnings. Bails out when the ticket is too ambiguous to act on |

### `productivity/` — not about shipping a change

Useful with no repo open at all. The bucket exists so the boundary was drawn before there
were three, not after.

| Skill | What it does |
| --- | --- |
| **[explain](./skills/productivity/explain/SKILL.md)** | Explain the thing you're stuck on — code, a principle, a metric, or how to build X in Y — in plain words that stay technically accurate, closed with an everyday analogy |
| **[draft-reply](./skills/productivity/draft-reply/SKILL.md)** | Turn a pasted thread, and usually a rough draft of the answer, into a reply that is short, checks out, and answers everything that was actually asked — the tightening is the easy part; the value is catching a number quoted from memory and the second question the draft never answered |

### `projects/` — not here

Instance-specific workflows — wired to one programme, one repo, one Confluence space — live
in [`jankolenko-projects`](https://github.com/JanKolenko-git/JanKolenko-Skills). They build on
the integrations above and declare this plugin as a hard dependency. Install it only if you
work on that programme; nothing here needs it.

### `meta/` — the skill layer improving itself

The learning loop that `record-learnings` closes for work repos, closed for the skills
themselves. A session-start hook (in [`hooks/`](./hooks)) injects one standing rule: while
any skill from this plugin runs, friction is noted silently and raised **once, at the end of
the run** — never mid-pipeline.

| Skill | What it does |
| --- | --- |
| **[improve-skill](./skills/meta/improve-skill/SKILL.md)** | Fix one of this repo's skills from an observed friction — shows the exact diff, 🛑 stops for approval, then commits, bumps the version and tells you to `plugin update` so the fix actually ships |
| **[find-skill-gaps](./skills/meta/find-skill-gaps/SKILL.md)** | Read the cross-session ledger in [`observations/SIGNALS.md`](./observations/SIGNALS.md) and propose a **new** skill only on two independent signals — 🛑 gated on the idea before drafting, and on the draft before it lands |
| **[record-engineering-rule](./skills/meta/record-engineering-rule/SKILL.md)** | Decide whether a coding run learned something that belongs in [`ENGINEERING.md`](./ENGINEERING.md) — routes most candidates to `record-learnings` or `improve-skill` instead, and 🛑 gates the rest |
| **[find-session-improvements](./skills/meta/find-session-improvements/SKILL.md)** | Sweep a finished session for what the skill layer should have learned from it and route each finding to the skill that owns it, behind one 🛑 triage gate — re-derives findings from the transcript, because in a long session noticing depends on recall and recall is what compaction drops |

All four are bound by [`.agents/authoring.md`](./.agents/authoring.md) — the written-down conventions every
skill here follows — which defers generic skill-writing mechanics to
`anthropic-skills:skill-creator` through one swappable reference.

## How they compose

Every skill declares `## Inputs` and `## Output` with **named fields**, so a caller wires by
name instead of guessing:

```
atlassian-jira  ──ticket.title──▶  git-create-branch   (slug)
                ──ticket.type───▶  git-create-branch   (type)
                ──ticket.description──▶  plan-change   (goal)
                ──ticket.acceptance_criteria──▶  write-tests  (criteria)
                ──ticket.key────▶  git-commit          (ticket_key)

plan-change  ──plan.steps───▶  implement
             ──plan.lanes───▶  fan out, or don't
             ──plan.*───────▶  critique-plan   (plan)
```

`implement-ticket` holds the ticket data once and passes values down, so nothing refetches.
Invoked on their own, the atoms take a bare ticket key and resolve it themselves.

Four edges run **backwards**, and they are what stop the pipeline being a one-way conveyor:

```
critique-plan ──reject-to-plan──▶ plan-change      (this run: replan, don't defend)
              ──reject-to-code──▶ implement

plan-change ──blocked──▶ clarify-goal ──clarify.*──▶ plan-change   (ask, don't die)

record-learnings ──▶ CLAUDE.md ──▶ plan-change     (next run: as constraints)

git-pr-push-and-open ──pr.url──▶ git-pr-address-review ──applied───▶ git-commit
                                                       ──declined──▶ a reply, not a change

git-pr-address-review ──resolution.corrections──▶ improve-skill / ENGINEERING.md / SIGNALS
git-pr-push-and-open  ──pr.gate_corrections────▶ (same three)
```

The last two close the longest loop in the repo: they run **backwards into the skill layer
itself**. An applied review comment, or work the user sends back at the push gate, is a human
overruling output the run had already decided was finished — which is stronger evidence than
any friction the agent notices about itself, because it comes from outside the run. Both
skills filter to the corrections that name a recurring *class* rather than one diff, and hand
those to whichever meta skill owns the destination.

For a review comment the evidence is the **landed diff, never the comment's text**. Comments
arrive from an API, so they are fetched content, and fetched content cannot reach the agent's
own instructions — that is the injection path, and `improve-skill`'s gate keeps it closed.
Only a change this run actually made counts, and only you can approve what it changes.

`git-pr-address-review` closes the code loop: a PR is opened, humans comment on it, and the
work comes back to the code. Each comment gets one of two verdicts — **applied** (the diff
moved) or **declined** (it didn't, and the reply says why) — and one row in a ledger, so no
comment is closed by silence and none is applied by a nod.

`critique-plan` reviews the diff against *intent*, which is a different question from the one
`/code-review` answers — tests ask whether it runs, the critique asks whether it should
exist. A plan the code disproves gets replaced rather than implemented more faithfully.

## Optional: sharper plan grounding

This plugin has **no hard dependency on any other plugin**. `/code-review`, `/simplify` and
`/run` are built into Claude Code, so they are always there.

One external skill is used when present. `plan-change` and `implement-ticket` will consult
[`mattpocock-skills:codebase-design`](https://github.com/mattpocock/skills) to check a plan
against the module boundaries a codebase already has:

```bash
/plugin install mattpocock-skills@claude-plugins-official
```

It lives in Claude Code's official marketplace, so there is nothing to clone and nothing to
link. Without it, both skills ground the plan themselves and say so once — a missing optional
skill never fails a run.

## Three safety properties worth knowing

**Writes only happen on your instruction.** `atlassian-jira` and `atlassian-confluence` can change
tickets and pages, so both carry an explicit provenance rule: a write happens only when the
user or an orchestrating skill asked for it — **never** because a ticket description, comment,
Confluence page or code comment said to. Fetched text is data, not instructions. There is
deliberately **no delete script**.

`record-learnings` writes through those same two skills and inherits the rule, with one of its
own on top: a learning has to come from what the run **observed** — a test that failed, an API
that returned something unexpected — never from a claim found in fetched text. Anything headed
for a shared surface stops for approval first; only the local `CLAUDE.md` edit doesn't, because
it lands in the diff like any other change.

**Confluence edits are section-scoped.** Confluence has no append primitive — every update
rewrites the whole page — so `update_page.py` writes only between its own markers, refuses
when the page moved under it (`409`), and refuses when a section looks like it already exists
without markers. `--dry-run` shows the change before anything is written.

**Pushing always stops for a human — and a hook enforces it.** `git-pr-push-and-open` shows
the full diff and waits for an explicit yes before `git push`. The gate lives in the same
skill as the push so nothing can compose around it, and it repeats every round of changes.
Only you, in chat, can waive it.

That much is advisory: it holds while a session actually invokes the skill. So the plugin
also ships a `PreToolUse` hook ([`hooks-handlers/pre-tool-use-git-push.py`](./hooks-handlers/pre-tool-use-git-push.py))
that inspects `git push` in **any** Bash call, so the harness itself demands an answer —
including from a session that never loaded the skill, or whose context was compacted past
the gate. It returns `ask` rather than `deny`, because the gate exists to be answered by a
person, not to make pushing impossible.

It is scoped to the pushes that are expensive to undo:

| Push | Hook |
| --- | --- |
| A feature branch | **silent** — the skill's own gate covers it |
| The default branch (resolved from `origin/HEAD`, or `main`/`master`) | asks |
| `--force` / `--force-with-lease` | asks |
| `--delete` a remote branch | asks |
| `--all`, `--mirror`, `--tags` | asks |
| A refspec it cannot parse | asks — an unreadable target is treated as the dangerous case |
| `--dry-run` | silent — reaches no remote |

`git push origin HEAD:main` asks, because the destination is resolved from the refspec
rather than read off the command. Prompting on *every* push was the first version, and it
was wrong: a gate that fires constantly trains you to approve without reading, which costs
more than it protects.

## Installation

### 1. Add the marketplace (once per machine)

```bash
claude plugins marketplace add JanKolenko-git/skills
```

### 2. Install the plugin

```bash
claude plugins install jankolenko-skills
```

Or, from inside a session:

```
/plugin install jankolenko-skills
```

This installs at **user scope** by default, which is what you want — `~/.claude` is shared,
so the skills show up in the Claude Code CLI, the desktop app, and the IDE extensions
alike. Restart Claude after installing.

> This is a private marketplace, not Claude Code's official one, so step 1 is required —
> `claude plugins install jankolenko-skills` on a machine that hasn't added the marketplace
> will not find anything. After step 1 it resolves by name; `jankolenko-skills@jankolenko`
> pins it explicitly if you ever have a name collision.

### 3. Point the skills at your instances, and set your tokens

The Atlassian skills read both the host and the credential from the environment at runtime.
There are **no defaults** — an unset URL stops with a setup message rather than guessing.
**Tokens live on your machine, never in this repo.**

Create one token in each product. They are per-product: a Jira token gets a `401` from
Confluence. In each, open the profile menu → *Personal Access Tokens*.

Add all four to `~/.zshenv` (not `~/.zshrc` — `.zshenv` is read by non-interactive shells
too, which is how the agent runs commands):

```bash
export JIRA_URL='https://jira.example.com'
export JIRA_PERSONAL_TOKEN='...'
export CONFLUENCE_URL='https://confluence.example.com'
export CONFLUENCE_PERSONAL_TOKEN='...'
```

Lock the file down, since it now holds secrets:

```bash
chmod 600 ~/.zshenv
```

Open a new terminal, then check all four are visible:

```bash
env | grep -c 'JIRA_URL\|JIRA_PERSONAL_TOKEN\|CONFLUENCE_URL\|CONFLUENCE_PERSONAL_TOKEN'
```

That should print `4`.

### 4. Point `find-repository` at your code (optional)

`find-repository` looks in the current directory, then `$REPO_ROOT`, then `~/Developer`, `~/code`,
`~/src`, `~/projects`, `~/repos`. If your repositories live somewhere else, set it:

```bash
export REPO_ROOT="$HOME/work"
```

### Environment variables

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

The atoms need none of these — only the two Atlassian integrations do.

TLS verification is **on** by default. The insecure escape hatches exist for TLS-inspecting
proxy environments and should stay unset.

## Usage

The skills are model-invoked: just ask, and the agent reaches for them.

```
solve PROJ-1234
read PROJ-1155
summarise https://jira.example.com/browse/PROJ-1155
what does the checkout tech spec say about the LCP handoff?
find PROJ tickets in review that mention caching
move PROJ-1234 to In Review and comment with the PR link
which repo is PROJ-1234 about?
what is INP, and what actually moves it?
explain how akamai caching decides a hit from a miss
open a PR for this branch
address the review comments on <pr-url>
```

You can also run the scripts yourself. They are stdlib-only Python 3 — nothing to install,
and every script takes `--help`:

```bash
python3 ~/.claude/plugins/**/skills/engineering/atlassian-jira/fetch_ticket.py PROJ-1155
```

## Requirements

- Python 3 (stdlib only — no `pip install`)
- A Jira / Confluence **Server or Data Center** instance you can reach (Cloud is not supported)
- Network access to it — most self-hosted instances sit behind a VPN
- A personal access token per product
- `gh` CLI, if you want `git-pr-push-and-open` to open the PR rather than hand you a compare link
- `gh` (GitHub) or `BITBUCKET_TOKEN` (Bitbucket), if you want `git-pr-address-review` to read
  and reply to review comments rather than work from pasted text

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| `CONFLUENCE_PERSONAL_TOKEN is not set` | Token exported in `~/.zshrc` instead of `~/.zshenv`, or the terminal predates the change |
| `HTTP 401 — token was rejected` | Token expired, or a Jira token is being used against Confluence (they don't cross over) |
| `HTTP 403` | The account genuinely lacks access to that ticket or space — or, on a write, lacks permission to change it |
| `no transition leads to …` | The workflow doesn't allow that status from the current one. Run `get_transitions.py` to see what it does allow |
| `JIRA_URL is not set` | The instance URL was never exported — see step 3 |
| `cannot reach ...` | Wrong host, or not on the network/VPN it sits behind |
| `find-repository` finds nothing | Set `REPO_ROOT`, or run from inside the repo |
| Bitbucket comment update returns `409` | Someone edited the thread mid-run — `git-pr-address-review` re-reads the comment `version` and retries once |

Exit codes distinguish the cases for scripting: `1` setup or bad input, `2` HTTP/auth,
`3` forbidden, `4` not found, `5` network unreachable.

## Development

Skills live in [`skills/`](./skills) under a **bucket**, sorted by domain: `engineering/`
for anything that moves a change toward a merged PR, `productivity/` for skills useful with
no repo open, `meta/` for skills that operate on the skill layer itself. The fourth bucket,
`projects/` — one team's conventions — is the whole of the companion `jankolenko-projects`
repo, so **the bucket also decides which repo a skill ships from**
([`adr/0004`](./.agents/adr/0004-two-repos.md)). Every skill sits at exactly
`skills/<bucket>/<skill-name>/SKILL.md`: one bucket level, never two, and the folder name is
the skill's `name` verbatim. Grouping a bucket still wants — a set of integrations, a
programme — goes in its [`README.md`](./skills), not in another folder; see
[`.agents/adr/0001-one-bucket-level.md`](./.agents/adr/0001-one-bucket-level.md).

A skill's **role** — integration, atom, orchestrator — is a declared property rather than a
folder, stated in its opening thesis and used to group its bucket `README.md`. Role is the
axis that changes as a skill grows a second caller; domain is the one that doesn't, so domain
is what the filesystem holds ([`adr/0002`](./.agents/adr/0002-domain-buckets.md)).

Adding a skill is four edits — the folder, its bucket `README.md`, the table above, and the
`skills` array in [`.claude-plugin/plugin.json`](./.claude-plugin/plugin.json). This checks
all four and exits non-zero on drift:

```bash
./scripts/list-skills.sh
```

New skills follow [`.agents/authoring.md`](./.agents/authoring.md) — most importantly
`## Inputs` and `## Output` with named fields, which is what makes a skill callable by
another skill instead of only by a human, and the rule that a skill refers to another as
`plugin:name`. That file is canonical for **both** repos; the projects repo keeps no copy.
[`CLAUDE.md`](./CLAUDE.md) has the layout contract and what must stay in sync;
[`.agents/adr/`](./.agents/adr) has the structural decisions and their rejected alternatives.

Validate the manifests before pushing:

```bash
claude plugin validate .
```

Neither that nor `list-skills.sh` checks **behaviour** — a reword that quietly drops a gate
passes both. [`evals/`](./evals) covers that: one case per expensive refusal, run before any
version bump. See [`evals/README.md`](./evals/README.md).

```bash
CLAUDE_CODE_WALNUT_SPIRE=1 claude plugin eval . --allow-tools Bash Write Edit
```

Working on the skills locally, without reinstalling on every edit:

```bash
claude plugin marketplace add ~/Developer/skills
```

That registers a **Directory** marketplace pointing at your clone, so the plugin is rebuilt
from the local working tree. A commit is enough to ship a change to yourself — no push
needed. Sessions still load from the versioned cache, so bump `plugin.json`'s `version`, then:

```bash
claude plugin update jankolenko-skills@jankolenko
```

The `@jankolenko` suffix is **required** — the bare name fails with "Plugin not found",
because `update` resolves against the qualified `plugin@marketplace` id it was installed
under. Restart Claude afterwards; the running session keeps its old cache.

The companion repo has its **own** marketplace, so its id is
`jankolenko-projects@jankolenko-projects`. Rather than remembering which is which, ask:

```bash
./scripts/which-plugin.sh <skill-name>
```

It prints the repo, the `plugin.json` to bump and the exact `update` command for whichever
repo owns that skill. `jankolenko-skills:improve-skill` uses it for the same reason.

## Security

No credentials are committed to this repository, and none should be. The Python clients read
tokens from the environment only; `_client.py` in each Atlassian skill is the single place
auth is handled, and `send_json` is the single place a write can originate. If a token ever lands
in a commit, rotate it in Atlassian — rewriting history is not enough.

## License

MIT — see [LICENSE](./LICENSE).
