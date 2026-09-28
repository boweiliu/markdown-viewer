---
title: "Markdown Viewer"
description: "Search and view markdown files from any directory, rendered with syntax highlighting"
thumbnail: "template.svg"
version: v1
format: v2
---

# Markdown Viewer

This file is the manifest for the **Markdown Viewer** template (slug:
`markdown-viewer`). It is the one document a future agent reads to understand,
present, and adapt this template. If you are an agent in a mind that was
created from this template, this file is your script: read all of it, then
follow "How to adapt it" below.

## What it is

A small web app that finds and displays markdown files. The user types part
of a filename into a search box; the app walks the workspace tree, lists every
`.md` file whose name matches, and opens the chosen one rendered as HTML --
headings, tables of contents, and code blocks with syntax highlighting --
instead of raw markdown source. There is no indexing step and nothing is
persisted: every search re-walks the filesystem, so newly written or edited
files show up immediately.

## How it works

The snapshot includes one path:

- `system/apps/md-viewer` -- the whole app: a single-file Flask service
  (`src/md_viewer/runner.py`) plus its `app.toml`, `pyproject.toml`, icon, and
  a ratchet test.

At runtime it is a synchronous Flask app served by threaded Werkzeug
(`run_simple`). It exposes four routes: `/` (the search page), `/search?q=`
(returns a list of matching files as an HTML fragment, filename-substring
match, case-insensitive, capped at 50 results), `/file/<path>` (renders one
file's markdown to HTML, using the `markdown` package's `toc` and
`codehilite` extensions), and `/health`. It searches `/home/user/workspace`
and `/home/user/workspace/.external_worktrees` recursively for `*.md` files;
`render_markdown` refuses to serve anything outside the workspace root or
anything that isn't a `.md` file. It listens on the port in `MD_VIEWER_PORT`
(default `8084`) and keeps no state of its own beyond `MD_VIEWER_DATA_DIR`,
which the app declares but does not currently use for anything persistent.

This snapshot does **not** include a `system/supervisord.conf.d/md-viewer.conf`
program entry or a `forward_port.py` port registration -- see "Requirements"
below for what wires it up so it can actually run as a window.

## Recipe

This template is version `v1`. It is not a fork of the
workspace it came from -- it is DERIVED from it by a recipe: include these
paths, leave these out, apply these published-version rules. An update re-runs
the recipe against the current workspace and publishes the result as the next
version, so anything excluded stays excluded even though it still exists in the
source workspace.

The recipe is machine-read, so it lives in the sibling
[`template.toml`](template.toml) -- its `[recipe]` table -- along with
the structured requirements and the environment this template needs
installed. That file is authoritative for all of it; this one holds the prose.

## Requirements

Everything the adopting mind must deal with before this template is really
theirs. Two kinds of entry, handled at different times:

- **Activation** -- what must be SET UP before anything runs, in the
  machine-readable `requires_` forms below. The adopting agent acts on these
  ITSELF, first, before asking anything.
- **Adaptation** -- what must be DECIDED or REWIRED, in prose. Worked through
  interactively with the user, after activation.

No `requires_permission`, `requires_secret`, or `requires_llm` lines -- the
app reads only local markdown files, calls no external service, and calls no
LLM.

- **Adaptation:** the app has no `system/supervisord.conf.d/md-viewer.conf`
  program entry or `forward_port.py` port registration -- only its own
  package (`system/apps/md-viewer`) is included. Give it a program entry
  (mirroring another simple Flask app such as `getting_started`) and register
  its port in `system/scripts/forward_port.py`, then
  `supervisorctl reread && supervisorctl update`, so it can be opened as a
  window.

## Environment

What this template needs INSTALLED, beyond what the template already has.
Declared in `template.toml`'s `[environment]` table; an adopting mind
converges it at ITS OWN pinned apt snapshot timestamp, so package versions come
out consistent with the rest of that mind's environment rather than frozen to
whatever this publisher happened to have.

Nothing extra -- runs on the stock workspace environment. The app's
dependencies (Flask, flask-sock, Werkzeug, markdown, pymdown-extensions) are
plain Python packages pulled in by its own `pyproject.toml` once it joins the
root `uv` workspace (`uv sync --all-packages`); it shells out to nothing and
uses no global npm/uv-tool/cargo binaries.

## How to adapt it

Instructions for the NEXT agent -- the one adapting this template into a
new mind. This is the `use-template` skill's template path; in short:

1. Read this entire file first, especially "Requirements" below. It holds two
   kinds of entry and they are handled at different times: the machine-readable
   `requires_` lines are ACTIVATION (set them up before anything runs), and
   the prose bullets are ADAPTATION (decide or rewire them afterwards).
2. Present the template to the user in plain, non-technical language: what
   it is, what it does, and what it needs from them (name the activation
   requirements).
3. Ask whether they want to use the same connectors (e.g. their own Slack).
   If YES: ACTIVATE FIRST -- initiate every `requires_permission` line NOW
   via a latchkey permission request (see the `latchkey` skill; the request
   opens the approval/login flow in the minds app), wire up any
   `requires_secret` values, start the services, and get the app showing
   THE USER'S OWN DATA. Done for a data-backed app means the user can open it
   and see their own data -- NOT that a service starts or an endpoint returns
   200. Then tell them it is live and to take a look.
4. Only AFTER that (or immediately, if they chose different connectors -- the
   swap is then the first adaptation) ask: "How do you want to adapt it?"
5. Work through each requirement interactively, one at a time. Translate each
   into plain language, ask for a decision only when you genuinely need one,
   and resolve the obvious ones yourself.
6. When done, append a dated entry to "Adaptation history" below (never
   rewrite earlier entries) and commit.

## Publication history

This template's changelog: what each published version changed. The PUBLISHER
appends one entry per version (newest last); earlier entries are never rewritten.
This is distinct from "Adaptation history" below, which is the ADOPTERS' log.

### v1 (2026-09-28) -- first publish: the markdown search-and-view app

## Adaptation history

Each mind that adapts this template appends one dated entry below. Earlier
entries are never rewritten.
