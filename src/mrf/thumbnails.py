"""Windows Explorer thumbnail helpers (no-op messaging on other OS)."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from mrf.tools import require_ffmpeg, require_ffprobe


def _poster_time(video: Path) -> str:
    ffprobe = require_ffprobe()
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        dur = float((proc.stdout or "").strip() or "0")
    except ValueError:
        dur = 0.0
    if dur > 0:
        t = min(3.0, max(0.5, dur * 0.05))
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = t % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}"
    return "00:00:01.000"


def embed_cover(file: Path) -> bool:
    ffmpeg = require_ffmpeg()
    tmp_video = Path(str(file) + ".thumbfix.tmp.mp4")
    tmp_poster = Path(str(file) + ".thumbfix.jpg")
    try:
        ss = _poster_time(file)
        subprocess.run(
            [ffmpeg, "-y", "-ss", ss, "-i", str(file), "-frames:v", "1", "-update", "1", "-q:v", "2", str(tmp_poster)],
            capture_output=True,
            check=False,
        )
        if not tmp_poster.is_file() or tmp_poster.stat().st_size < 1024:
            return False
        proc = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(file),
                "-i",
                str(tmp_poster),
                "-map",
                "0",
                "-map",
                "1",
                "-c",
                "copy",
                "-disposition:v:1",
                "attached_pic",
                "-movflags",
                "+faststart",
                str(tmp_video),
            ],
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0 or not tmp_video.is_file():
            return False
        tmp_video.replace(file)
        file.touch()
        return True
    finally:
        tmp_poster.unlink(missing_ok=True)
        tmp_video.unlink(missing_ok=True)


def clear_explorer_thumbnail_cache() -> int:
    if sys.platform != "win32":
        return 0
    import os

    cache_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Explorer"
    removed = 0
    for pat in ("thumbcache_*.db", "iconcache_*.db", "thumbcache_idx.db"):
        for p in cache_dir.glob(pat):
            try:
                p.unlink()
                removed += 1
            except OSError:
                pass
    subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"], capture_output=True, check=False)
    time.sleep(1)
    subprocess.Popen(["explorer.exe"])
    return removed


def fix_thumbnails(
    directory: Path | str,
    *,
    recursive: bool = False,
    embed_cover_flag: bool = False,
    cache_only: bool = False,
) -> dict[str, int]:
    root = Path(directory)
    if not root.is_dir():
        raise FileNotFoundError(f"Directory not found: {root}")

    pattern = "**/*.mp4" if recursive else "*.mp4"
    files = sorted(root.glob(pattern))
    embedded = 0
    if embed_cover_flag and not cache_only:
        require_ffmpeg()
        for f in files:
            if embed_cover(f):
                embedded += 1

    for f in files:
        try:
            f.touch()
        except OSError:
            pass

    removed = clear_explorer_thumbnail_cache() if sys.platform == "win32" else 0
    return {"files": len(files), "embedded": embedded, "cache_removed": removed}
