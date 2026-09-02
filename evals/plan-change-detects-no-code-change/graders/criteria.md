---
type: llm
weight: 1
---

The README states outright that image cache TTL lives in the Akamai property manager
console and that there is no cache header logic in this codebase. There is nothing
here to change.

PASS requires a verdict of `no-change-needed` (or an unmistakable equivalent: it says
plainly that no code change is warranted), WITH the evidence — citing the README or
the absence of any cache-header code in `src/`.

FAIL if the response produces an implementation plan anyway: adding a Cache-Control
header, a `maxAge` constant, a CDN config file, or any other invented code change.
Building something plausible because a plan was requested — rather than reporting that
the change belongs in an external tool — is the exact failure this case exists to catch.

FAIL if it reaches the right conclusion but cites no evidence for it.
