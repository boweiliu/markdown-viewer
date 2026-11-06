#!/usr/bin/env bash
set -euo pipefail

python3 system/scripts/forward_port.py --manifest system/apps/markdown_viewer/app.toml --url http://127.0.0.1:8097
export MD_VIEWER_PORT=8097
exec uv run --no-project --with-editable .external_worktrees/markdown-viewer/system/apps/md-viewer md-viewer
