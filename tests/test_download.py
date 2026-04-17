"""Tests for the resumable file downloader.

Uses a small in-process HTTP server that supports Range requests so tests can
exercise fresh download, resume, and checksum verification without network.
"""

import hashlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from empirical_incubation import download


class _RangeHandler(BaseHTTPRequestHandler):
    content: bytes = b""

    def do_GET(self):  # noqa: N802
        total = len(self.content)
        range_header = self.headers.get("Range", "")
        if range_header.startswith("bytes="):
            spec = range_header[len("bytes=") :]
            start_s, _, end_s = spec.partition("-")
            start = int(start_s) if start_s else 0
            end = int(end_s) if end_s else total - 1
            body = self.content[start : end + 1]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
        else:
            body = self.content
            self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args, **_kwargs):
        pass


@pytest.fixture
def mock_server():
    content = b"".join(bytes([i % 256]) for i in range(4096))
    _RangeHandler.content = content
    server = HTTPServer(("127.0.0.1", 0), _RangeHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield {
            "url": f"http://127.0.0.1:{port}/file.bin",
            "content": content,
            "sha256": hashlib.sha256(content).hexdigest(),
        }
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_download_fresh_writes_full_file(tmp_path: Path, mock_server):
    dest = tmp_path / "file.bin"

    download.download_file(mock_server["url"], dest)

    assert dest.read_bytes() == mock_server["content"]


def test_download_verifies_sha256(tmp_path: Path, mock_server):
    dest = tmp_path / "file.bin"

    download.download_file(mock_server["url"], dest, expected_sha256=mock_server["sha256"])

    assert dest.read_bytes() == mock_server["content"]


def test_download_raises_on_sha256_mismatch(tmp_path: Path, mock_server):
    dest = tmp_path / "file.bin"

    with pytest.raises(download.ChecksumMismatch):
        download.download_file(mock_server["url"], dest, expected_sha256="0" * 64)


def test_download_resumes_partial_file(tmp_path: Path, mock_server):
    dest = tmp_path / "file.bin"
    partial = dest.with_suffix(dest.suffix + ".part")
    # Simulate an interrupted download — first half already on disk.
    half = len(mock_server["content"]) // 2
    partial.write_bytes(mock_server["content"][:half])

    download.download_file(mock_server["url"], dest)

    assert dest.read_bytes() == mock_server["content"]
    assert not partial.exists(), "partial file should be renamed/cleaned after completion"


def test_download_skips_when_destination_already_correct(tmp_path: Path, mock_server):
    dest = tmp_path / "file.bin"
    dest.write_bytes(mock_server["content"])
    mtime_before = dest.stat().st_mtime_ns

    download.download_file(mock_server["url"], dest, expected_sha256=mock_server["sha256"])

    assert dest.stat().st_mtime_ns == mtime_before, "must not re-download when content matches"
