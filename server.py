#!/data/data/com.termux/files/usr/bin/python
"""A Windows-Explorer-shaped file browser for your phone's own storage,
served locally and opened in Chrome. Read-only on purpose -- browsing
and opening files, not a second way to delete things.

    fileexplorer              starts the server, opens Chrome to it
    fileexplorer --port 9000  same, on a port you choose
    fileexplorer --no-open    just start the server, print the URL

Listens on 127.0.0.1 only (same reasoning as Spark's own editor
server) -- nothing outside your phone can reach it, even on shared
wifi. Rooted at /storage/emulated/0 ("internal storage" -- the normal
Android equivalent of "This PC"), not the whole filesystem: Termux's
own app data and the rest of Android's private storage stay out of
reach of a browser tab on purpose.
"""
import argparse
import html
import mimetypes
import subprocess
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path("/storage/emulated/0").resolve()
HERE = Path(__file__).resolve().parent
DEFAULT_PORT = 8790


def safe_resolve(raw_path):
    """Turns a client-supplied path into a real path INSIDE root, or
    raises ValueError. The one thing standing between a browser tab and
    reading arbitrary files on the phone, so this is deliberately strict:
    resolve symlinks/.. first, then check containment, not the other way
    around (checking the unresolved string first is the classic way this
    kind of check gets bypassed)."""
    candidate = (ROOT / raw_path.lstrip("/")).resolve() if raw_path else ROOT
    if candidate != ROOT and ROOT not in candidate.parents:
        raise ValueError("outside root")
    return candidate


class Handler(BaseHTTPRequestHandler):
    server_version = "fileexplorer/1"

    def log_message(self, fmt, *args):
        pass  # the default prints every request to stderr -- noisy, skip it

    def _send_json(self, obj, status=200):
        import json
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status, message):
        self._send_json({"error": message}, status=status)

    def _send_file_response(self, path):
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        size = path.stat().st_size
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(size))
        self.end_headers()
        with path.open("rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def _send_static(self, filename, content_type):
        path = HERE / filename
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/":
            self._send_static("index.html", "text/html; charset=utf-8")
            return

        if parsed.path == "/api/list":
            raw = query.get("path", [""])[0]
            try:
                target = safe_resolve(raw)
            except ValueError:
                self._send_error_json(403, "outside root")
                return
            if not target.is_dir():
                self._send_error_json(404, "not a folder")
                return
            entries = []
            try:
                for item in target.iterdir():
                    try:
                        stat = item.stat()
                    except OSError:
                        continue
                    entries.append({
                        "name": item.name,
                        "is_dir": item.is_dir(),
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                    })
            except PermissionError:
                self._send_error_json(403, "permission denied")
                return
            entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))
            rel = "" if target == ROOT else str(target.relative_to(ROOT))
            self._send_json({"path": rel, "entries": entries})
            return

        if parsed.path == "/api/file":
            raw = query.get("path", [""])[0]
            try:
                target = safe_resolve(raw)
            except ValueError:
                self._send_error_json(403, "outside root")
                return
            if not target.is_file():
                self._send_error_json(404, "not a file")
                return
            try:
                self._send_file_response(target)
            except PermissionError:
                self._send_error_json(403, "permission denied")
            return

        self.send_response(404)
        self.end_headers()


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--no-open", action="store_true", help="don't launch Chrome automatically")
    args = p.parse_args()

    if not ROOT.is_dir():
        sys.exit("storage root not found: %s (not running in real Termux?)" % ROOT)

    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = "http://127.0.0.1:%d/" % args.port
    print("file explorer serving %s at %s" % (ROOT, url))
    print("Ctrl-C to stop.")

    if not args.no_open:
        try:
            subprocess.run(["termux-open", "--chooser", url], check=False)
        except FileNotFoundError:
            print("(termux-open not found -- open %s in a browser yourself)" % url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
