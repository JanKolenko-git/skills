# Hosts

Per-host commands for the three things `git-pr-address-review` needs: **read** the comments,
**reply** to a thread, **resolve** a thread. Read only the section for the host in front of
you.

Tokens are read from the environment at runtime. Never hardcode one, and never ask the user
to paste one into chat — if it is missing or rejected, say which variable is needed and stop.

| Host | Detect by | Auth |
| --- | --- | --- |
| GitHub | `github.com/<owner>/<repo>/pull/<n>` | `gh auth status` |
| Bitbucket Cloud | `bitbucket.org/<workspace>/<repo>/pull-requests/<n>` | `BITBUCKET_TOKEN` |
| Bitbucket Data Center | any other host, `/projects/<KEY>/repos/<slug>/pull-requests/<n>` | `BITBUCKET_TOKEN`, `BITBUCKET_URL` |

Bitbucket's two flavours share a name and nothing else — different URL shape, different API
version, different JSON. Confirm which one you are on from the URL before issuing a call.

---

## GitHub

`gh` covers reading and replying. Thread resolution is GraphQL-only.

**Read** — three separate sources, and a review is usually spread across all three:

```bash
# PR metadata and the diff
gh pr view <pr> --json title,body,state,files,baseRefName,headRefName
gh pr diff <pr>

# Top-level conversation comments
gh pr view <pr> --comments

# Inline review comments — file, line and thread id, which the above does not give you
gh api repos/<owner>/<repo>/pulls/<n>/comments --paginate \
  --jq '.[] | {id, path, line, user: .user.login, in_reply_to_id, body}'
```

**Unresolved threads** — `include: unresolved` needs GraphQL; the REST endpoint has no
resolved flag:

```bash
gh api graphql -f query='
  query($owner:String!, $repo:String!, $n:Int!) {
    repository(owner:$owner, name:$repo) {
      pullRequest(number:$n) {
        reviewThreads(first:100) {
          nodes {
            id isResolved isOutdated
            comments(first:20) { nodes { databaseId path line author{login} body } }
          }
        }
      }
    }
  }' -F owner=<owner> -F repo=<repo> -F n=<n>
```

`isOutdated: true` is the **stale** signal from Step 1 — the code moved under the comment.

**Reply** in a thread — `<comment-id>` is the `databaseId` of the thread's *first* comment:

```bash
gh api repos/<owner>/<repo>/pulls/<n>/comments/<comment-id>/replies \
  -f body="<reply text>"
```

A top-level (non-inline) comment is answered with `gh pr comment <pr> --body "<text>"`.

**Resolve** a thread — `<thread-id>` is the node `id` from the query above, not a number:

```bash
gh api graphql -f query='
  mutation($id:ID!) {
    resolveReviewThread(input:{threadId:$id}) { thread { isResolved } }
  }' -F id=<thread-id>
```

---

## Bitbucket Cloud

API v2.0 at `https://api.bitbucket.org`. Auth: `Authorization: Bearer $BITBUCKET_TOKEN`.

**Read** — inline comments carry `inline.path` and `inline.to`; general ones have no
`inline` key. `deleted: true` comments still come back and must be skipped:

```bash
curl -sS -H "Authorization: Bearer $BITBUCKET_TOKEN" \
  "https://api.bitbucket.org/2.0/repositories/<workspace>/<repo>/pullrequests/<n>/comments?pagelen=100" \
  | jq '.values[] | select(.deleted != true) | {
      id, parent: .parent.id, user: .user.display_name,
      path: .inline.path, line: .inline.to,
      resolved: (.resolution != null), text: .content.raw
    }'
```

Paginate by following `.next` until it is absent.

**Reply** — the `parent` id threads it; omit `parent` and you start a new thread:

```bash
curl -sS -X POST -H "Authorization: Bearer $BITBUCKET_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.bitbucket.org/2.0/repositories/<workspace>/<repo>/pullrequests/<n>/comments" \
  -d '{"content": {"raw": "<reply text>"}, "parent": {"id": <comment-id>}}'
```

**Resolve** — only the thread's root comment can be resolved:

```bash
curl -sS -X POST -H "Authorization: Bearer $BITBUCKET_TOKEN" \
  "https://api.bitbucket.org/2.0/repositories/<workspace>/<repo>/pullrequests/<n>/comments/<comment-id>/resolve"
```

---

## Bitbucket Data Center

API v1.0 at `$BITBUCKET_URL` (self-hosted, e.g. `https://bitbucket.example.com`).
Auth: `Authorization: Bearer $BITBUCKET_TOKEN` — an HTTP access token, not a password.

**Read** — comments arrive through the *activities* feed, not a comments endpoint. Replies
are nested under `comments[]` on each comment, so recurse rather than reading one level:

```bash
BASE="$BITBUCKET_URL/rest/api/1.0/projects/<KEY>/repos/<slug>/pull-requests/<n>"

curl -sS -H "Authorization: Bearer $BITBUCKET_TOKEN" "$BASE/activities?limit=100" \
  | jq '.values[] | select(.action == "COMMENTED") | {
      id: .comment.id, version: .comment.version,
      user: .comment.author.displayName,
      path: .commentAnchor.path, line: .commentAnchor.line,
      state: .comment.state, text: .comment.text,
      replies: [.comment.comments[]? | {id, version, text, state}]
    }'
```

`state` is `OPEN` or `RESOLVED` — that is the `include: unresolved` filter. Paginate on
`isLastPage` / `nextPageStart`.

**Reply**:

```bash
curl -sS -X POST -H "Authorization: Bearer $BITBUCKET_TOKEN" \
  -H "Content-Type: application/json" "$BASE/comments" \
  -d '{"text": "<reply text>", "parent": {"id": <comment-id>}}'
```

**Resolve** — an update needs the comment's **current `version`**, and a stale one returns
`409`. Re-read the comment for its version immediately before the update; do not reuse the
version from a fetch made earlier in the run:

```bash
curl -sS -X PUT -H "Authorization: Bearer $BITBUCKET_TOKEN" \
  -H "Content-Type: application/json" "$BASE/comments/<comment-id>" \
  -d '{"version": <version>, "state": "RESOLVED"}'
```

A `409` means someone edited the thread while you were working. Re-read and retry once; if it
conflicts again, report it and leave the thread open rather than looping.
