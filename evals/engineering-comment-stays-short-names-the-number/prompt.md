---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit]
---

The gallery images in `src/components/image-grid.tsx` carry a `srcSet` but no `sizes`, so
the browser assumes `100vw` and downloads the largest candidate. Add an exported
`IMAGE_SIZES` string to `src/constants.ts` and pass it as `sizes`.

The layout is in `src/styles/image-grid.module.scss`: from the gallery breakpoint the grid
is two equal columns beside the sticky sidebar, with the page capped at its max width; below
it the carousel slide spans the viewport. The grid subtracts the scrollbar and `sizes`
should not, because an understated slot makes Chrome pick a smaller candidate and that
costs LCP.
