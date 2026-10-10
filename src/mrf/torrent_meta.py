"""Parse `aria2c -S` torrent metadata (no download)."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from mrf.tools import require_aria2


@dataclass
class TorrentFile:
    index: int
    path: str
    size: int
    ext: str
    is_padding: bool


@dataclass
class TorrentMeta:
    hash: str
    name: str
    total_bytes: int
    files: list[TorrentFile] = field(default_factory=list)
    raw: str = ""

    @property
    def real_files(self) -> list[TorrentFile]:
        return [f for f in self.files if not f.is_padding]

    @property
    def padding_files(self) -> list[TorrentFile]:
        return [f for f in self.files if f.is_padding]


_RE_HASH = re.compile(r"Info Hash:\s*([a-fA-F0-9]{40})")
_RE_NAME = re.compile(r"(?m)^Name:\s*(.+)$")
_RE_TOTAL = re.compile(r"Total Length:\s*[^\(]*\(([\d,]+)\)")
_RE_FILE = re.compile(r"^\s*(\d+)\|(.+)$")
_RE_SIZE = re.compile(r"\(([\d,]+)\)")


def aria2_show(torrent_path: Path | str) -> str:
    aria2 = require_aria2()
    proc = subprocess.run(
        [aria2, "-S", str(torrent_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if "Info Hash:" not in out:
        raise RuntimeError(f"aria2c -S failed for {torrent_path}")
    return out


def parse_listing(listing: str) -> TorrentMeta:
    hash_m = _RE_HASH.search(listing)
    name_m = _RE_NAME.search(listing)
    total_m = _RE_TOTAL.search(listing)
    info_hash = hash_m.group(1).lower() if hash_m else "?"
    name = name_m.group(1).strip() if name_m else "?"
    total_bytes = int(total_m.group(1).replace(",", "")) if total_m else 0

    files: list[TorrentFile] = []
    lines = listing.splitlines()
    for i, line in enumerate(lines):
        m = _RE_FILE.match(line)
        if not m:
            continue
        idx = int(m.group(1))
        path = m.group(2).strip()
        size = 0
        if i + 1 < len(lines):
            sm = _RE_SIZE.search(lines[i + 1])
            if sm:
                size = int(sm.group(1).replace(",", ""))
        leaf = Path(path.replace("\\", "/")).name
        ext = Path(leaf).suffix.lower()
        is_padding = ("padding_file" in path) or leaf.startswith("_____padding")
        files.append(
            TorrentFile(index=idx, path=path, size=size, ext=ext, is_padding=is_padding)
        )

    return TorrentMeta(
        hash=info_hash, name=name, total_bytes=total_bytes, files=files, raw=listing
    )


def load_meta(torrent_path: Path | str) -> TorrentMeta:
    return parse_listing(aria2_show(torrent_path))


def media_file_indices(meta: TorrentMeta, *, videos_only_mp4: bool = True) -> list[int]:
    """Indices suitable for aria2 --select-file (1-based as in aria2 -S)."""
    out: list[int] = []
    for f in meta.real_files:
        if videos_only_mp4:
            if f.ext == ".mp4" and "jpg" not in f.path.lower() and "snapshot" not in f.path.lower() and "thumbs" not in f.path.lower():
                out.append(f.index)
        elif f.ext in {".mp4", ".mkv", ".avi", ".mov", ".m4v", ".webm"}:
            out.append(f.index)
    return out
