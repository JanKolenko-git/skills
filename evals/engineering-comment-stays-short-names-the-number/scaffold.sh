#!/usr/bin/env bash
# Builds the scratch repository this case runs in. The eval runner executes it in the
# sandbox before the agent's first turn (pass --scaffold), so the prompt carries only the task.
set -euo pipefail

git init -q . && git config user.email e@x && git config user.name n && \
mkdir -p src/components src/styles && \
printf '{\n  "name": "gallery-app",\n  "private": true,\n  "dependencies": {"react": "19.1.0"}\n}\n' > package.json && \
cat > src/constants.ts <<'TS'
export const GALLERY_BREAKPOINT_PX = 960

export const PAGE_LOAD_MAX_TIME_MS = 1000
TS
cat > src/styles/image-grid.module.scss <<'SCSS'
.page {
  display: flex;
  max-width: 1920px;
  margin: 0 auto;
}

.carousel {
  width: 100vw;
  overflow-x: auto;
}

.sidebar {
  position: sticky;
  top: 0;
  flex: none;
  width: 370px;

  @media (min-width: 1280px) {
    width: 434px;
  }

  @media (min-width: 1440px) {
    width: 480px;
  }
}

.grid {
  display: grid;
  flex: 1;
  grid-template-columns: repeat(2, 1fr);
  width: calc(100% - var(--scrollbar-width, 0px));
}
SCSS
cat > src/components/image-grid.tsx <<'TSX'
import { useSyncExternalStore } from 'react'
import { GALLERY_BREAKPOINT_PX } from '../constants'
import styles from '../styles/image-grid.module.scss'

type GalleryImage = { src: string; srcSet: string; alt: string }

const gridQuery = `(min-width: ${GALLERY_BREAKPOINT_PX}px)`

function useIsGrid() {
  return useSyncExternalStore(
    (onChange) => {
      const media = window.matchMedia(gridQuery)
      media.addEventListener('change', onChange)
      return () => media.removeEventListener('change', onChange)
    },
    () => window.matchMedia(gridQuery).matches,
    () => true
  )
}

export function ImageGrid({ images }: { images: GalleryImage[] }) {
  const isGrid = useIsGrid()
  const items = images.map((image) => (
    <img key={image.src} src={image.src} srcSet={image.srcSet} alt={image.alt} />
  ))
  return isGrid ? (
    <div className={styles.page}>
      <div className={styles.grid}>{items}</div>
      <aside className={styles.sidebar} />
    </div>
  ) : (
    <div className={styles.carousel}>{items}</div>
  )
}
TSX
git add -A && git commit -qm init && ls -R src
