"""Resumable, checksum-verified HTTP downloader.

A completed file lives at `dest`; a partial download lives at `dest + ".part"`
with resume via the `Range` header on the next run. Skips re-downloading when
`dest` already matches the expected sha256 (or simply exists, when no checksum
is provided).
"""

import hashlib
import urllib.request
from pathlib import Path

_CHUNK = 64 * 1024


class ChecksumMismatch(RuntimeError):
    pass


def download_file(
    url: str,
    dest: Path,
    *,
    expected_sha256: str | None = None,
    chunk_size: int = _CHUNK,
) -> Path:
    dest = Path(dest)
    partial = dest.with_suffix(dest.suffix + ".part")
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        if expected_sha256 is None or _sha256(dest) == expected_sha256:
            return dest

    start = partial.stat().st_size if partial.exists() else 0
    headers = {"Range": f"bytes={start}-"} if start > 0 else {}
    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req) as resp:
        mode = "ab" if start > 0 else "wb"
        with open(partial, mode) as f:
            while chunk := resp.read(chunk_size):
                f.write(chunk)

    partial.replace(dest)

    if expected_sha256 is not None:
        got = _sha256(dest)
        if got != expected_sha256:
            raise ChecksumMismatch(
                f"{dest.name}: expected sha256 {expected_sha256}, got {got}"
            )

    return dest


def download_all(
    urls: list[str],
    dest_dir: Path,
    *,
    expected_sha256: dict[str, str] | None = None,
) -> list[Path]:
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    for url in urls:
        name = url.rsplit("/", 1)[-1]
        sha = (expected_sha256 or {}).get(url)
        out.append(download_file(url, dest_dir / name, expected_sha256=sha))
    return out


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(_CHUNK):
            h.update(chunk)
    return h.hexdigest()
