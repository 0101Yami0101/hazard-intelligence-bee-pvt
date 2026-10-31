# Codebase map

An interactive, visual map of SlopeSense (this repo, LandSlideFlood), for understanding it without reading the code: what exists, what's planned, how the parts connect and why. It opens with the big picture and goes as deep as you want, down to every file, function, table, setting and test.

**Live link:** https://claude.ai/artifact/Ej7MuYSgwAVFoNotfhyFEa (private to its owner until shared from claude.ai)

Open `index.html` straight from disk to view it locally. No build step or server is needed.

## How it's made

| File | What it is | Edit it? |
|---|---|---|
| `content.mjs` | The plain-English layer: the parts on the big picture, journeys, file and folder descriptions, milestones, glossary | **Yes.** Updates go here |
| `map.config.mjs` | Scanner settings: which code to read, where the schema and env vars are | When the repo's layout changes |
| `data.js` | Everything the page shows: `content.mjs` plus facts scanned from the repo | Never by hand. The scanner writes it |
| `code.js` | The Functions tab: every Python function, class and setting, what each calls, decides and touches, and the source | Never by hand. The scanner writes it |
| `index.html` | The viewer: HTML, CSS and JavaScript, no libraries | Only to change how the map looks |
| [`scripts/codebase-map/`](../../scripts/codebase-map/) | The scanner (`scan.mjs`) and function scanners (`code.mjs`, and `code_py.py` for Python) | Rarely. Upgrade with the codebase-map skill |

The scanner collects these facts, so they can't drift from the repo:

- **Code:** files and line counts, which file imports which, tests and their names, and routes.
- **Functions** (Python, read with Python's own parser by `code_py.py`; it never runs the code):
  - every function's inputs, result, calls and callers;
  - its decisions, loops, errors and returns, in the order they run;
  - the files it reads and writes, network calls, other programs it runs, and what it draws on screen;
  - its entry points: the Streamlit app, the scripts (with the command from their docstring), the Modal schedule, web link and commands.
- **Data:** tables and columns from Drizzle/Payload snapshots, Prisma schemas or SQL files.
- **Config:** env var names (never values), including the ones Python code reads through `os.environ`, `os.getenv` or the `credential()` helper (`envReaders` in `map.config.mjs`), CI jobs, Docker services, and package scripts and versions.
- **Docs:** ADRs, plus the rules section of `CLAUDE.md` or `AGENTS.md`.
- **History:** git commits.

It reads only files Git tracks or would track (untracked files count unless `.gitignore` excludes them), so `.env`, `data/` and other ignored files are never read.

## Updating it

Update the map at the end of each phase, and whenever a part of the system, route, table, flow, env var or service is added or removed.

1. **Edit `content.mjs`.** Add or change the parts, journeys, file descriptions and so on.
2. **Run `node scripts/codebase-map/scan.mjs`** (this repo has no package.json, so there is no `npm run map`). It writes `data.js` and `code.js` and lists anything undescribed or broken. Add `--todo` to list everything still to describe.
3. **Run `node scripts/codebase-map/scan.mjs --check`.** It also fails if `data.js` or `code.js` is out of date.
4. **Open `index.html` locally and look.**
5. **Republish to the same link** (below). Commit `content.mjs`, `data.js` and `code.js` with the change.

To upgrade the scanner and viewer to the codebase-map skill's latest version, ask Claude to "update the codebase map tooling". This keeps `content.mjs`.

## Publishing

It's a multi-file page:

- **`index.html`** is the page;
- **`data.js` and `code.js`** are published beside it.

In a Claude Code session, ask Claude to publish or republish the codebase map. Claude reads the published page first, then publishes `index.html` with the two data files to the same link, so everyone who has the link sees the update.

## Safety

The map is meant to be published.

- **Never put secrets in `content.mjs`:** no passwords, keys, private endpoints or customer data.
- **The scanner reads env var names only,** never their values.
- **`code.js` contains the Python source code,** so anyone with the link can read the code.
- **File names are published,** including business papers under `docs/` (their contents are not).
