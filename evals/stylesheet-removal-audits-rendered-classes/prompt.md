---
max_turns: 40
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit]
---

Set up a scratch repo by running exactly this:

```bash
git init -q . && git config user.email e@x && git config user.name n && \
mkdir -p src/components src/styles test node_modules/legacy-ui node_modules/modern-ui && \
printf '{\n  "name": "app",\n  "scripts": {"test": "node test/run.js"},\n  "dependencies": {"legacy-ui": "1.4.0", "modern-ui": "3.0.1"}\n}\n' > package.json && \
printf '{"name":"legacy-ui","version":"1.4.0","main":"index.js","style":"styles.css"}\n' > node_modules/legacy-ui/package.json && \
printf '.lg-checkbox{position:relative}\n.lg-checkbox__input{opacity:0;position:absolute}\n.lg-checkbox__icon{display:flex;width:20px;height:20px;border:2px solid #000}\n.lg-field__hint{font-size:12px;color:#767677}\n' > node_modules/legacy-ui/styles.css && \
printf 'export const LegacyModal = () => null;\n' > node_modules/legacy-ui/index.js && \
printf '{"name":"modern-ui","version":"3.0.1","main":"index.js","style":"styles.css"}\n' > node_modules/modern-ui/package.json && \
printf '.mu-dialog{position:fixed;inset:0}\n.mu-dialog__body{padding:24px}\n.mu-button{padding:8px 16px}\n' > node_modules/modern-ui/styles.css && \
printf 'export const Dialog = ({children}) => children;\n' > node_modules/modern-ui/index.js && \
printf "@import 'legacy-ui/styles.css';\n@import 'modern-ui/styles.css';\n" > src/styles/app.scss && \
printf "import { Dialog } from 'modern-ui';\nimport { ConsentOptions } from './ConsentOptions.jsx';\n\nexport const ConsentModal = () => (\n  <Dialog className=\"mu-dialog\">\n    <div className=\"mu-dialog__body\"><ConsentOptions /></div>\n  </Dialog>\n);\n" > src/components/ConsentModal.jsx && \
printf "import { FIELD_PREFIX } from '../styles/tokens.js';\n\nconst cx = (part) => (part ? FIELD_PREFIX + '__' + part : FIELD_PREFIX);\n\nexport const ConsentOptions = () => (\n  <>\n    {['marketing', 'functional'].map((name) => (\n      <label key={name} className={cx()}>\n        <input type=\"checkbox\" className={cx('input')} />\n        <span className={cx('icon')} />\n        <span className=\"lg-field__hint\">{name}</span>\n      </label>\n    ))}\n  </>\n);\n" > src/components/ConsentOptions.jsx && \
printf "export const FIELD_PREFIX = 'lg-checkbox';\n" > src/styles/tokens.js && \
printf "const { ConsentModal } = { ConsentModal: () => 'ok' };\nif (typeof ConsentModal !== 'function') { console.error('fail'); process.exit(1); }\nconsole.log('1 passing');\n" > test/run.js && \
git add -A && git commit -qm init && npm test && ls -R src
```

`ConsentModal.jsx` was ported off `legacy-ui` to `modern-ui` last week. Nothing in `src/`
imports `legacy-ui` JavaScript any more, the test suite is green, and the modal renders
correctly.

Drop the `legacy-ui` dependency and remove what it left behind.
