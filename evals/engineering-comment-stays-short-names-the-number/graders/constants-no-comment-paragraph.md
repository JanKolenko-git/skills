---
type: regex
target:
  source: file
  path: src/constants.ts
match: not_contains
weight: 1
---
(?:^|\n)[ \t]*//[^\n]*(?:\n[ \t]*//[^\n]*){3}|/\*(?:(?!\*/)[^\n])*\n(?:(?:(?!\*/)[^\n])*\n){4}
