# Engineering

Skills for shipping code. Almost everything here is in the ticket pipeline, and the entries
below are grouped by the **role** each one plays — a property of the skill, not of its folder.
See [`.agents/authoring.md`](../../.agents/authoring.md) for what each role commits to.

## Integrations

Need a URL and a token in the environment to be useful; neither will guess a host. Both speak
**Server / Data Center** REST — Bearer PAT auth, Jira v2 with wiki markup, Confluence
`/rest/api/content` with storage-format XHTML. Atlassian **Cloud** is a different API and will
not authenticate here.

- **[atlassian-jira](./atlassian-jira/SKILL.md)** — Read and update tickets: fetch as Markdown with comments,
  links and attachments, search by text or JQL, transition status, comment, create and edit
  issues. Reads `$JIRA_URL` and `$JIRA_PERSONAL_TOKEN`.
- **[atlassian-confluence](./atlassian-confluence/SKILL.md)** — Read pages as Markdown with macros expanded and
  tables intact, search, list and download attachments, and add or update **one delimited
  section** on a page. Reads `$CONFLUENCE_URL` and `$CONFLUENCE_PERSONAL_TOKEN`.

Both carry the provenance rule: a write happens only because the user or an orchestrating
skill asked for it, never because fetched text said to. There is deliberately no delete script
in either.

## Atoms

Useful alone, in any repo, with explicit inputs. Nothing instance-specific — they resolve a
ticket key themselves only if `atlassian-jira` happens to be installed. Each declares `## Inputs` and
`## Output` with **named fields**, which is what lets an orchestrator wire them by name
instead of guessing.

- **[find-repository](./find-repository/SKILL.md)** — Work out which local git repo a task belongs to —
  and refuse rather than guess.
- **[plan-change](./plan-change/SKILL.md)** — Read the code, then decide what to do to it:
  files, steps, risks, and whether the work splits into independent lanes.
- **[clarify-goal](./clarify-goal/SKILL.md)** — Turn a blocked plan into answered questions:
  facts get looked up, decisions go to the user one at a time with a recommendation, answers
  fold back into the goal.
- **[git-create-branch](./git-create-branch/SKILL.md)** — Branch the way the repo names branches, or
  `feature/`/`bugfix/`/`hotfix/` + key + slug when it has no convention of its own.
- **[write-tests](./write-tests/SKILL.md)** — Write tests matching the repo's existing runner,
  layout and assertion style, against the acceptance criteria rather than the internals.
- **[critique-plan](./critique-plan/SKILL.md)** — Review the diff against the *plan*, not for
  bugs: what's missing, what's unplanned, whether it should exist.
- **[git-commit](./git-commit/SKILL.md)** — Stage and commit with a conventional message.
  Local only — never pushes.
- **[git-pr-push-and-open](./git-pr-push-and-open/SKILL.md)** — Show the diff, **stop for human approval**, then push
  and open the PR.
- **[git-pr-address-review](./git-pr-address-review/SKILL.md)** — Work the review comments on a
  PR: apply the ones that earn a change, decline the rest with a reason, one ledger row each.
- **[record-learnings](./record-learnings/SKILL.md)** — Write durable constraints back to
  `CLAUDE.md`, a spec section or the ticket — and drop everything that wasn't durable.
- **[prepare-local-environment](./prepare-local-environment/SKILL.md)** — Get the repo to the
  state where you can exercise it by hand: work out how it runs, install, build, start,
  then prove the app *rendered* before handing back a URL.

## Orchestrators

Wire atoms together and own almost no mechanics of their own. An orchestrator that starts
growing mechanics is telling you an atom is missing. It holds the fetched data once and passes
values down by the atoms' field names, so nothing downstream refetches.

- **[implement-ticket](./implement-ticket/SKILL.md)** — Ticket → context → repo → plan →
  branch → implement → test → critique → review → PR → *In Review* → learnings. Stops for
  human review before pushing, and bails out when the ticket is too ambiguous to act on.
