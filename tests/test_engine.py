"""Smoke tests for the html-dashboard engine server."""
import importlib.util
import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "server.py"
_spec = importlib.util.spec_from_file_location("dash_server", ENGINE)
dash = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dash)


def _get(base, path):
    with urllib.request.urlopen(base + path, timeout=2) as r:
        return r.status, json.loads(r.read().decode() or "null")


def _post(base, path, obj):
    data = json.dumps(obj).encode()
    req = urllib.request.Request(
        base + path, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=2) as r:
        return r.status, json.loads(r.read().decode() or "null")


@pytest.fixture
def server(tmp_path):
    html = tmp_path / "demo-dash.html"
    html.write_text("<html><body>hello-dash</body></html>")
    cfg = dash.DashConfig(
        html_path=html,
        state_file=tmp_path / "state.json",
        replies_file=tmp_path / "replies.json",
        ping_file=tmp_path / "ping.json",
    )
    httpd, port = dash.serve(cfg, "127.0.0.1", 8800)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(base + "/health", timeout=0.5)
            break
        except urllib.error.URLError:
            time.sleep(0.02)
    yield base
    httpd.shutdown()


def test_redact_jwt_and_keys():
    payload = {
        "note": "token eyJhbGciOiJ.eyJzdWIiOiIx.SflKxwRJ here",  # gitleaks:allow (synthetic fixture)
        "cfg": "SERVICE_PROD_API_KEY=supersecretvalue123",  # gitleaks:allow (synthetic fixture)
        "auth": "Authorization: apikey abcdef0123456789",  # gitleaks:allow (synthetic fixture)
    }
    out = dash.redact(payload)
    assert "REDACTED-JWT" in out["note"]
    assert "eyJzdWIiOiIx" not in out["note"]
    assert "supersecretvalue123" not in out["cfg"]
    assert "REDACTED-KEY" in out["cfg"]
    assert "abcdef0123456789" not in out["auth"]


def test_serves_html(server):
    with urllib.request.urlopen(server + "/", timeout=2) as r:
        body = r.read().decode()
    assert "hello-dash" in body


def test_health(server):
    status, body = _get(server, "/health")
    assert status == 200 and body["ok"] is True


def test_state_roundtrip_and_redacts(server):
    _post(server, "/state", {"a": 1, "leak": "SERVICE_API_KEY=zzzzzzsecret"})  # gitleaks:allow (synthetic fixture)
    status, body = _get(server, "/state")
    assert status == 200 and body["a"] == 1
    assert "zzzzzzsecret" not in json.dumps(body)


def test_reply_roundtrip(server):
    _, posted = _post(server, "/reply", {"testId": "c1", "level": "info", "text": "hi"})
    rid = posted["id"]
    _, all_replies = _get(server, "/replies")
    assert any(r["text"] == "hi" for r in all_replies)
    _, since = _get(server, "/replies/since/0")
    assert any(r["id"] == rid for r in since)


def test_ping_roundtrip(server):
    _post(server, "/ping", {"testId": "c2"})
    status, body = _get(server, "/ping")
    assert status == 200 and body["testId"] == "c2" and "ts" in body


def test_find_free_port_skips_taken():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    taken = s.getsockname()[1]
    try:
        chosen = dash.find_free_port("127.0.0.1", taken)
        assert chosen != taken
    finally:
        s.close()
