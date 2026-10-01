# The hypothesis panel

Read when `panel` is set, or when Step 5 has refuted every hypothesis of a list the session
ranked alone: the next list from the same context re-ranks the same suspects, so a stuck run
seats the panel once, unasked, on `panel`'s models or the default `haiku, sonnet, opus`.
`panel: none` never seats one.

Print `3 agents: haiku, sonnet, opus, read-only, ≈ <3 × 50K + reads>K` first, `reads` the
bytes of the brief divided by four, per seat. Then one `Agent` call per model in a single
message, `subagent_type: jankolenko-skills:panelist`, `model` set per call, all on the same
brief:

- The three symptom lines.
- The loop command with its red output.
- The minimised repro and the files it touches.
- On a stuck run, each refuted hypothesis with its experiment and its result.
- The ask: three to five ranked, falsifiable hypotheses, each with its refuting experiment.

Merge into one list, a hypothesis two models name ahead of one only one names, and drop any
that restates a refuted one. Each seat opens with the model it runs on. Two the same is one
model twice, not a panel, so say so. An `Agent` tool without a `model` parameter: say so once
and continue alone. Instrumenting and the fix stay in the session, and the panel seats itself
at most once per run.
