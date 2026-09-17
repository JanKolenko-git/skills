---
name: template-skill
description: <What the skill does, in the third person>. Use when <the phrases users type>. <One near-miss, if a competing skill exists: "Pushing is git-pr-push-and-open".>
argument-hint: <required> [optional]
---

# Template Skill

<One or two sentences stating the skill's opinion. See spec/authoring.md for the contract.>

## Inputs

- `input` — **required.** <What it is, and where a caller gets it.>
- `option` — optional. <What it changes; the default.>

## Output

| Field | Contents |
| --- | --- |
| `template.verdict` | <What a caller reads back, by this name> |

## Step 1 — <Imperative>

<What to do, one instruction per sentence.>

Done when: <something checkable>.

## Step 2 — 🛑 <Only if the next action is expensive to undo>

> 🛑 **GATE — <what is about to happen>.** <The artefact is on screen.>
> Ask through `AskUserQuestion`: "<a question only answerable by looking at it>" — options
> **approve**, **change**, **stop**.
> approve → Step 3. change → redo Step 1 with the answer, then this gate again.
> stop → end, with <what is left ready>.
> <One sentence of why this gate exists.> Standing rule: <the one that applies>.

## Step 3 — <Imperative>

<What to do.>

Done when: <something checkable>.

## Notes

- <What the skill deliberately does not do, and which skill does.>
