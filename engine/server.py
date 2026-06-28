#!/usr/bin/env python3
"""Generalized localhost dashboard server for the html-dashboard skill.

Serves a generated dashboard HTML and mediates two-way state between the
browser (where the operator works) and Claude Code (which reads state via
Bash and posts replies the page renders inline). Configured entirely via
DASH_* env vars.

Endpoints:
  GET  /                     -> the dashboard HTML
  GET  /state                -> current state JSON
  POST /state                -> save state from the page (redacted)
  GET  /replies              -> all replies from Claude
  GET  /replies/since/<id>   -> replies with id > given id (polling)
  POST /reply                -> Claude posts a reply (redacted)
  POST /ping                 -> operator pings an element (redacted)
  GET  /ping                 -> last ping marker
  GET  /health               -> liveness probe
  GET  /assets/<name>        -> vendored static asset (mermaid/css/js)

Env:
  DASH_HTML    explicit HTML file to serve (overrides DASH_DIR scan)
  DASH_DIR     dir to scan for newest *-dash.html (default: cwd)
  DASH_PORT    preferred port (default 8765; auto-increments if taken)
  DASH_HOST    bind host (default 127.0.0.1)
  DASH_STATE_FILE / DASH_REPLIES_FILE / DASH_PING_FILE  override /tmp paths
"""
import dataclasses
import json
import os
import re
import socket
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# --- Redaction ----------------------------------------------------------
# Three base64-url segments joined by dots, starting with the "eyJ" header.
_JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")
_APIKEY_RE = re.compile(r"(?i)\bapikey\s+[A-Za-z0-9._-]{12,}")
_ENVKEY_RE = re.compile(r"(?i)([A-Z][A-Z0-9_]*_API_KEY\s*[=:]\s*)\S+")


def redact(value):
    """Scrub JWTs and API keys from any value before it is persisted."""
    if isinstance(value, str):
        value = _JWT_RE.sub("<REDACTED-JWT>", value)
        value = _APIKEY_RE.sub("apikey <REDACTED-KEY>", value)
        value = _ENVKEY_RE.sub(r"\1<REDACTED-KEY>", value)
        return value
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    return value


# --- Config + helpers ------------------------------------------------------
ASSETS_DIR = Path(__file__).parent / "assets"
_ASSET_TYPES = {
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".map": "application/json; charset=utf-8",
}


class DashConfig:
    html_path: Path
    state_file: Path
    replies_file: Path
    ping_file: Path


DashConfig = dataclasses.dataclass(DashConfig)


def resolve_html(dash_dir: Path, override: str | None) -> Path:
    """Serve the explicit DASH_HTML, else newest *-dash.html in dash_dir."""
    if override:
        return Path(override)
    candidates = sorted(dash_dir.glob("*-dash.html"))
    if candidates:
        return candidates[-1]
    raise SystemExit(
        f"no *-dash.html in {dash_dir}; set DASH_HTML to an explicit file"
    )


def config_from_env() -> DashConfig:
    dash_dir = Path(os.environ.get("DASH_DIR", os.getcwd()))
    html_path = resolve_html(dash_dir, os.environ.get("DASH_HTML"))
    stem = html_path.stem
    return DashConfig(
        html_path=html_path,
        state_file=Path(os.environ.get("DASH_STATE_FILE", f"/tmp/dash-{stem}-state.json")),
        replies_file=Path(os.environ.get("DASH_REPLIES_FILE", f"/tmp/dash-{stem}-replies.json")),
        ping_file=Path(os.environ.get("DASH_PING_FILE", f"/tmp/dash-{stem}-ping.json")),
    )


def find_free_port(host: str, start: int, span: int = 25) -> int:
    """Return the first free port at or after `start` (probes by binding)."""
    for port in range(start, start + span):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"no free port in [{start}, {start + span})")


def read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return default


def write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


# --- Request handler -------------------------------------------------------
def make_handler(cfg: DashConfig):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            if args and isinstance(args[-1], str) and args[-1].startswith("2"):
                if "POST" not in (fmt % args):
                    return
            sys.stderr.write("[dash] %s - %s\n" % (self.address_string(), fmt % args))

        def _send_json(self, status, body):
            payload = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)

        def _send_bytes(self, status, data: bytes, ctype: str):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _read_body(self) -> bytes:
            length = int(self.headers.get("Content-Length", "0"))
            return self.rfile.read(length) if length > 0 else b""

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                if not cfg.html_path.exists():
                    self._send_bytes(500, f"HTML missing: {cfg.html_path}".encode(), "text/plain")
                    return
                self._send_bytes(200, cfg.html_path.read_bytes(), "text/html; charset=utf-8")
                return
            if path.startswith("/assets/"):
                name = path[len("/assets/"):]
                asset = (ASSETS_DIR / name).resolve()
                if ASSETS_DIR.resolve() not in asset.parents or not asset.is_file():
                    self._send_bytes(404, b"asset not found", "text/plain")
                    return
                ctype = _ASSET_TYPES.get(asset.suffix, "application/octet-stream")
                self._send_bytes(200, asset.read_bytes(), ctype)
                return
            if path == "/state":
                self._send_json(200, read_json(cfg.state_file, {}))
                return
            if path == "/replies":
                self._send_json(200, read_json(cfg.replies_file, []))
                return
            if path.startswith("/replies/since/"):
                since = path.rsplit("/", 1)[-1]
                replies = read_json(cfg.replies_file, [])
                self._send_json(200, [r for r in replies if str(r.get("id", "")) > str(since)])
                return
            if path == "/ping":
                self._send_json(200, read_json(cfg.ping_file, {}))
                return
            if path == "/health":
                self._send_json(200, {"ok": True, "ts": time.time()})
                return
            self._send_bytes(404, f"not found: {path}".encode(), "text/plain")

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            body = self._read_body()
            if path == "/state":
                try:
                    data = json.loads(body or b"{}")
                except json.JSONDecodeError:
                    self._send_json(400, {"error": "invalid json"})
                    return
                write_json(cfg.state_file, redact(data))
                self._send_json(200, {"ok": True})
                return
            if path == "/ping":
                try:
                    data = json.loads(body or b"{}")
                except json.JSONDecodeError:
                    data = {}
                data = redact(data)
                data["ts"] = time.time()
                write_json(cfg.ping_file, data)
                self._send_json(200, {"ok": True, "ts": data["ts"]})
                return
            if path == "/reply":
                try:
                    reply = json.loads(body or b"{}")
                except json.JSONDecodeError:
                    self._send_json(400, {"error": "invalid json"})
                    return
                reply = redact(reply)
                replies = read_json(cfg.replies_file, [])
                reply.setdefault("id", str(int(time.time() * 1000)))
                reply.setdefault("ts", time.time())
                replies.append(reply)
                write_json(cfg.replies_file, replies)
                self._send_json(200, {"ok": True, "id": reply["id"]})
                return
            self._send_bytes(404, f"not found: {path}".encode(), "text/plain")

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

    return Handler


def serve(cfg: DashConfig, host: str, port: int):
    """Build a ThreadingHTTPServer on the first free port >= `port`.

    Returns (httpd, actual_port). Caller runs serve_forever().
    """
    for f, default in [(cfg.state_file, {}), (cfg.replies_file, []), (cfg.ping_file, {})]:
        if not f.exists():
            write_json(f, default)
    actual = find_free_port(host, port)
    httpd = ThreadingHTTPServer((host, actual), make_handler(cfg))
    return httpd, actual


def main() -> None:
    cfg = config_from_env()
    host = os.environ.get("DASH_HOST", "127.0.0.1")
    port = int(os.environ.get("DASH_PORT", "8765"))
    httpd, actual = serve(cfg, host, port)
    sys.stderr.write(f"[dash] serving on http://{host}:{actual}\n")
    sys.stderr.write(f"[dash] HTML:    {cfg.html_path}\n")
    sys.stderr.write(f"[dash] state:   {cfg.state_file}\n")
    sys.stderr.write(f"[dash] replies: {cfg.replies_file}\n")
    sys.stderr.write(f"[dash] ping:    {cfg.ping_file}\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("\n[dash] shutting down\n")
        httpd.shutdown()


if __name__ == "__main__":
    main()
