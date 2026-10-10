"""Verify MP4 files with ffprobe."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from mrf.tools import require_ffprobe


@dataclass
class VerifyResult:
    path: Path
    ok: bool
    detail: str = ""


def verify_dir(directory: Path | str, *, recursive: bool = False) -> list[VerifyResult]:
    root = Path(directory)
    if not root.is_dir():
        raise FileNotFoundError(f"Directory not found: {root}")

    ffprobe = require_ffprobe()
    pattern = "**/*.mp4" if recursive else "*.mp4"
    files = sorted(root.glob(pattern))
    results: list[VerifyResult] = []

    for f in files:
        if f.stat().st_size < 1024 * 1024:
            results.append(
                VerifyResult(f, False, f"too small or incomplete ({f.stat().st_size} bytes)")
            )
            continue
        proc = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(f),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0 or not (proc.stdout or "").strip():
            results.append(VerifyResult(f, False, "ffprobe failed (possibly corrupt)"))
        else:
            results.append(VerifyResult(f, True, (proc.stdout or "").strip()))
    return results
