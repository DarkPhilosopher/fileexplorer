# fileexplorer

A Windows-Explorer-shaped file browser for your phone's own storage —
a folder tree on the left, a file list on the right, breadcrumbs along
the top — served locally by Termux and opened in Chrome. Built to go
with [termux-bin](https://github.com/DarkPhilosopher/termux-bin)'s
`organize-files`, so there's a real way to *look* at the result.

```
fileexplorer
```

Starts a local server and opens it in Chrome. `--port N` to pick a
different port, `--no-open` to just print the URL.

## What it is, and isn't

- **Read-only.** You can browse and open files (they open in a new
  tab, so Chrome's own image/video/PDF/text viewers handle them) —
  there's no delete, move, or rename button anywhere in it. Pairs with
  `organize-files`'s own "delete nothing" rule rather than undoing it.
- **Offline, local-only.** `server.py` listens on `127.0.0.1` only —
  same reasoning as Spark's own editor server — so nothing outside
  your phone can reach it, even on shared wifi. No external
  JS/CSS libraries either; `index.html` is one self-contained file.
- **Rooted at `/storage/emulated/0`** ("internal storage" — the normal
  Android equivalent of "This PC"), not the whole filesystem. Termux's
  own app data and the rest of Android's private storage stay out of
  reach of a browser tab on purpose. Every path a client sends is
  resolved and checked against that root server-side before anything
  is read, so a crafted `../../` request can't walk outside it.

## What's in here

| File | What it does |
|---|---|
| `server.py` | The whole backend — stdlib only, no dependencies. `/api/list?path=` lists a folder, `/api/file?path=` streams a file's raw bytes. |
| `index.html` | The whole frontend — folder tree sidebar, file list, breadcrumbs. Self-contained, no build step. |

## Why not just use a file manager app

Because it's genuinely useful to have the same offline, no-install,
no-permissions-prompt shape as everything else in this family of
tools — same reasoning `spark browser`/`spark2` open straight in
Chrome instead of being native apps.
