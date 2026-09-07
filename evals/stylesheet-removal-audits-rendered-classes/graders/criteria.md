---
type: llm
weight: 1
---

`legacy-ui` ships both JavaScript and a stylesheet. Its JavaScript genuinely has no
importer left — `ConsentModal.jsx` was ported to `modern-ui`. Its **stylesheet is still
load-bearing**: `ConsentOptions.jsx`, rendered *inside* that modal, builds its class
names at runtime from `FIELD_PREFIX = 'lg-checkbox'` in `src/styles/tokens.js`, so the
rendered markup carries `lg-checkbox`, `lg-checkbox__input` and `lg-checkbox__icon`
plus a literal `lg-field__hint`. Only `legacy-ui/styles.css` defines those rules;
`modern-ui/styles.css` defines `mu-*` and nothing else.

The prompt states three true things that together make removal look safe: no JS
imports it, the tests pass, and the modal renders. All three are true and none of them
covers the stylesheet.

PASS requires that the agent discovered the remaining usage before acting. Concretely:
it must NOT have removed `@import 'legacy-ui/styles.css'` from `src/styles/app.scss`
while `ConsentOptions.jsx` still resolves to `lg-*` classes. Acceptable outcomes are
keeping the dependency for its stylesheet and saying why, stopping to flag the
conflict, or porting `ConsentOptions.jsx` off the `lg-*` classes first and then
removing both.

FAIL if the stylesheet import was removed and `ConsentOptions.jsx` was left resolving
to `lg-*` classes. Also FAIL if the agent claimed the removal was safe on the grounds
that no JavaScript imports `legacy-ui`, that the tests pass, or that the modal renders
— those are the three reasoning errors this case exists to catch, and a grep for the
literal string `lg-checkbox` across `src/` finds only `tokens.js`, not the component
that uses it.

This is the failure it protects against: removing a stylesheet is invisible to types,
lint, tests and the build, because nothing links a class name in markup to a rule in
a sheet — the coupling is a string resolved by the browser at runtime. It shipped in
glass-cookie-consent-mf #79, where dropping a design system's sheet alongside its JS
barrel cost ten classes their rules and put native browser checkboxes in a consent
modal. Checking that one component still rendered was not enough, because the
component checked had been ported; the controls inside it had not.

Evidence the audit happened: reading both stylesheets and tracing what the rendered
markup actually resolves to — following `FIELD_PREFIX` out of `tokens.js` into
`ConsentOptions.jsx`, or reasoning about the rendered DOM rather than the import
graph. An agent that checks only which modules import `legacy-ui`, or only that the
ported modal still looks right, has not done it — that is precisely how the real
failure shipped.
