<p align="center">
  <img alt="Markdown Viewer" src="template.svg" width="480">
</p>

# Markdown Viewer

<p align="center">
  <a href="https://boweiliu.github.io/open-in-minds/?git_url=https://github.com/boweiliu/markdown-viewer"><img alt="Open in Mind" height="64" src="https://img.shields.io/badge/Open%20in%20Mind-D8D1C0?style=for-the-badge"></a>
</p>

Didn't work? Create a Mind workspace and paste this to your agent:
` /use-template https://github.com/boweiliu/markdown-viewer`

## Why you care

Digging through a project for the right markdown file -- notes, specs, READMEs,
changelogs -- usually means either remembering the exact path or grepping from
a terminal. This gives you a search box instead: type part of a filename, get
a list of matches, click one, and read it as formatted HTML (headings, tables
of contents, syntax-highlighted code blocks) rather than raw markdown source.

## How to use it

Open the app and type part of a filename into the search box (matching is a
case-insensitive substring of the filename, not the file's contents). Results
list every `.md` file found, with its path shown underneath. Click a result to
render it as HTML; a "Search Files" link at the top takes you back. There are
no accounts, settings, or configuration -- it searches the whole workspace
tree fresh on every request.

## Ideas for making it yours

- Match against file contents as well as filenames, so a search can find a
  file by what's written in it, not just its name.
- Add breadcrumbs or a directory tree alongside the flat search results, for
  browsing rather than only searching.
- Limit the search roots to a configurable allowlist of directories instead of
  the whole workspace.
- Add a dark/light theme toggle to the rendered page.
- Cache the rendered HTML per file (keyed on mtime) if the workspace grows
  large enough that a full tree walk on every search feels slow.

## What this is

This repository is a published **minds template**: a clean, bootable
snapshot of what a mind built, ready to adapt into your own. It is NOT the
generic workspace template -- it is this specific project.

[`template.md`](template.md) is the full manifest -- what it is, how it
works, what it needs to run, and what to adapt -- with the
machine-readable half (recipe, requirements, and the environment it needs
installed) in [`template.toml`](template.toml).
