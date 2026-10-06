#!/data/data/com.termux/files/usr/bin/bash
# Creates the `fileexplorer` bare command. Run once after cloning this
# repo on a phone that doesn't have it yet:
#
#     bash install.sh
#
# Safe to re-run any time.
set -euo pipefail
TARGET="/data/data/com.termux/files/usr/bin/fileexplorer"

{
  echo '#!/data/data/com.termux/files/usr/bin/sh'
  echo "# CATALOG: fileexplorer -- Windows-Explorer-style offline file browser, opens in Chrome (127.0.0.1 only)"
  echo "# A thin launcher so \`fileexplorer\` works as a bare command -- the"
  echo "# actual script lives at ~/fileexplorer/server.py."
  echo 'exec python3 "$HOME/fileexplorer/server.py" "$@"'
} > "$TARGET"
chmod +x "$TARGET"
echo "installed -- try: fileexplorer"
