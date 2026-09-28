"""Search and view markdown files as HTML.

Services run from /home/user/workspace (the repo root). Conventions:

- Persistent state (anything written and read across runs -- cursors,
  caches, snapshots, user records): read and write it under ``DATA_DIR``
  (defined below), never a hardcoded ``data/.apps/md-viewer/`` at the
  call site. ``DATA_DIR`` defaults to ``data/.apps/md-viewer/`` but
  honors the ``MD_VIEWER_DATA_DIR`` env var, so an editing agent can point a
  throwaway instance at a *copy* of the data instead of the live store
  (see the update-app skill). Do NOT use ``Path(__file__)``-based
  paths for state -- the bug to avoid is one process writing to
  ``/home/user/workspace/data/.apps/...`` while another reads from
  ``/home/user/workspace/system/apps/<pkg>/data/...``.
- Static assets shipped alongside this file (templates, default
  configs, bundled JSON): ``Path(__file__).parent / "assets/..."`` is
  fine and is the right pattern.
- Listen port: bind ``PORT`` (defined below), which defaults to this
  app's assigned port but honors the ``MD_VIEWER_PORT`` env var, so
  an editing agent can boot a throwaway instance on a *spare* port
  alongside the live one (see the update-app skill). Never hardcode
  the port at the ``run_simple`` call.

This is a synchronous Flask app served by the threaded Werkzeug server.
The app owns its own browser origin (the forwarder routes
``http://md-viewer.<workspace-host>/`` straight to this port), so it serves
at ``/`` and root-absolute URLs, cookies, and service workers all work
unmodified -- nothing rewrites anything. Use ``flask_sock`` if you need
WebSockets.
"""

import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from flask import Flask, Response, abort, send_file, request
from werkzeug.serving import run_simple
import markdown
from markdown.extensions import toc, codehilite

# Persistent state for this app lives under DATA_DIR. It defaults to
# ``data/.apps/md-viewer/`` but is overridable via the ``MD_VIEWER_DATA_DIR`` env var
# so a throwaway instance can run against a *copy* of the data while editing --
# see the update-app skill. Always read/write state through DATA_DIR;
# never hardcode ``data/.apps/md-viewer/`` at a call site, or the override is
# bypassed. A writing call site should ``DATA_DIR.mkdir(parents=True,
# exist_ok=True)`` before writing.
DATA_DIR = Path(os.environ.get("MD_VIEWER_DATA_DIR", "data/.apps/md-viewer"))

# Listen port. Defaults to this app's assigned port but is overridable via
# the ``MD_VIEWER_PORT`` env var so an editing agent can boot a throwaway
# instance on a spare port next to the live one (see the update-app skill).
# Never hardcode the port at the ``run_simple`` call, or the override is bypassed.
PORT = int(os.environ.get("MD_VIEWER_PORT", "8084"))

# The browser-side modules the workspace shell builds and every app serves from
# its own origin: the app contract (how a page talks to the shell framing it) and
# the element context menu (the right-click menu whose last rows hand the
# clicked element to a chat). A module import is a fetch without cookies, which
# the forwarder refuses across origins, so they are served here rather than from
# the shell. Relative to the repo root the service runs from, like DATA_DIR.
SHELL_STATIC_MODULES_DIR = Path("system/apps/system_interface/imbue/system_interface/static/_static")
SHELL_STATIC_MODULE_NAMES = ('app_contract.js', 'context_menu.js')

# The script every page serves (keep it on every page): it connects the page to
# the shell, reports where the page is on the handshake so the shell can reopen
# this app's window at the same place, and installs the element context menu.
# A page visited outside the shell runs it harmlessly: nothing arrives, and the
# menu's Explain and Modify rows grey out.
SHELL_PAGE_SCRIPT = """<script type="module">
  import { connectToShell } from "/_static/app_contract.js";
  import { installElementContextMenu } from "/_static/context_menu.js";
  let handshake = null;
  const connection = connectToShell({
    onHandshake: (received) => {
      handshake = received;
      connection.location(location.pathname + location.search, document.title);
    },
  });
  installElementContextMenu({ connection, handshake: () => handshake });
</script>"""

WORKSPACE_ROOT = Path("/home/user/workspace")
SEARCH_PATHS = [
    WORKSPACE_ROOT,
    WORKSPACE_ROOT / ".external_worktrees",
]

app = Flask("md_viewer", static_folder=None)


def find_markdown_files(query: str) -> list[tuple[str, Path]]:
    query_lower = query.lower()
    results = []
    for search_path in SEARCH_PATHS:
        if not search_path.exists():
            continue
        for md_file in search_path.rglob("*.md"):
            if query_lower in md_file.name.lower():
                rel_path = md_file.relative_to(WORKSPACE_ROOT)
                results.append((str(rel_path), md_file))
    return sorted(results, key=lambda x: x[0])


def render_markdown(file_path: Path) -> str:
    if not file_path.is_file():
        abort(404)
    if not file_path.suffix.lower() == ".md":
        abort(400)
    if not str(file_path.resolve()).startswith(str(WORKSPACE_ROOT.resolve())):
        abort(403)

    content = file_path.read_text(encoding="utf-8")
    md = markdown.Markdown(
        extensions=[toc.TocExtension(), codehilite.CodeHiliteExtension()]
    )
    html_body = md.convert(content)

    title = file_path.stem
    return f"""<!doctype html><html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; color: #333; }}
  pre {{ background: #f4f4f4; padding: 12px; border-radius: 4px; overflow-x: auto; }}
  code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 2px; font-family: monospace; }}
  pre code {{ background: none; padding: 0; }}
  h1, h2, h3 {{ margin-top: 24px; }}
  a {{ color: #0066cc; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .nav {{ margin: 20px 0; padding: 12px; background: #f8f8f8; border-radius: 4px; }}
  .nav a {{ margin-right: 16px; }}
</style>
</head><body>
<div class="nav">
  <a href="/">Search Files</a>
</div>
<h1>{title}</h1>
{html_body}
{SHELL_PAGE_SCRIPT}
</body></html>"""


@app.route("/")
def index() -> Response:
    return Response(
        """<!doctype html><html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>md-viewer</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
  h1 { margin-top: 0; }
  .search-box { display: flex; gap: 8px; margin-bottom: 20px; }
  input { flex: 1; padding: 12px; font-size: 16px; border: 1px solid #ddd; border-radius: 4px; }
  button { padding: 12px 20px; font-size: 16px; background: #0066cc; color: white; border: none; border-radius: 4px; cursor: pointer; }
  button:hover { background: #0052a3; }
  .results { margin-top: 20px; }
  .result { padding: 12px; border: 1px solid #eee; border-radius: 4px; margin-bottom: 8px; }
  .result a { color: #0066cc; text-decoration: none; display: block; font-weight: 500; }
  .result a:hover { text-decoration: underline; }
  .path { color: #666; font-size: 12px; margin-top: 4px; }
  .loading { color: #666; font-style: italic; }
</style>
</head><body>
<h1>Markdown Viewer</h1>
<div class="search-box">
  <input type="text" id="search-input" placeholder="Search for markdown files..." autofocus />
  <button type="button" id="search-btn">Search</button>
</div>
<div class="results" id="results"></div>
""" + SHELL_PAGE_SCRIPT + """
<script>
  const input = document.getElementById('search-input');
  const btn = document.getElementById('search-btn');
  const resultsDiv = document.getElementById('results');
  let searchTimeout;

  async function doSearch() {
    const q = input.value.trim();
    if (!q) {
      resultsDiv.innerHTML = '';
      return;
    }

    resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
    try {
      const resp = await fetch('/search?q=' + encodeURIComponent(q));
      const html = await resp.text();
      resultsDiv.innerHTML = html || '<div class="loading">No files found.</div>';
    } catch (err) {
      resultsDiv.innerHTML = '<div class="loading">Error searching.</div>';
    }
  }

  btn.addEventListener('click', doSearch);
  input.addEventListener('keyup', (e) => {
    if (e.key === 'Enter') {
      doSearch();
    } else {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(doSearch, 500);
    }
  });
</script>
</body></html>""",
        mimetype="text/html",
    )


@app.route("/search")
def search() -> Response:
    q = request.args.get("q", "").strip()
    if not q or len(q) < 1:
        return Response("", mimetype="text/html")

    results = find_markdown_files(q)

    if not results:
        return Response("<p>No markdown files found.</p>", mimetype="text/html")

    html = ""
    for rel_path, full_path in results[:50]:
        encoded_path = rel_path.replace("\\", "/")
        html += f"""<div class="result">
  <a href="/file/{encoded_path}">{rel_path}</a>
  <div class="path">{full_path.parent}</div>
</div>"""

    return Response(html, mimetype="text/html")


@app.route("/file/<path:file_path>")
def view_file(file_path: str) -> Response:
    safe_path = WORKSPACE_ROOT / file_path
    return Response(render_markdown(safe_path), mimetype="text/html")


@app.route("/_static/<basename>")
def shell_module(basename: str) -> Response:
    # The two shell-built modules and nothing else: a name that is not one of
    # them is a 404, so this route can never read outside that directory.
    if basename not in SHELL_STATIC_MODULE_NAMES:
        abort(404)
    module_path = SHELL_STATIC_MODULES_DIR / basename
    if not module_path.is_file():
        abort(404)
    # Flask resolves a relative path against the app's own directory, not the cwd.
    return send_file(module_path.absolute(), mimetype="text/javascript")


@app.route("/health")
def health() -> Response:
    return Response('{"status": "ok"}', mimetype="application/json")


def main() -> None:
    run_simple(
        "127.0.0.1", PORT, app, threaded=True, use_reloader=False, use_debugger=False
    )


if __name__ == "__main__":
    main()
