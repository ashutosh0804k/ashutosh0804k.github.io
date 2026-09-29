"""Serve the site locally so the tests run against exactly what's in the repo."""

import functools
import http.server
import threading
from pathlib import Path

import pytest

SITE_ROOT = Path(__file__).resolve().parent.parent
LIVE_URL = "https://ashutosh0804k.github.io/"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def base_url():
    handler = functools.partial(QuietHandler, directory=str(SITE_ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
