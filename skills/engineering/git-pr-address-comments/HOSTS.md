# Hosts

The commands for the three things `git-pr-address-comments` needs: **read** the comments,
**reply** to a thread, **resolve** a thread.

GitHub is the only host covered, detected by `github.com/<owner>/<repo>/pull/<n>`, and `gh`
carries the auth. On any other host, say so and work from comment text the user pastes.
Never ask for a token in chat: if `gh auth status` fails, name that and stop.

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

