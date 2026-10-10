"""Hard-timeout seeder probe (always kills aria2 + clears temp)."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from mrf.constants import TRACKERS_CSV
from mrf.process_util import kill_aria2_matching, rmtree_quiet, run_with_timeout
from mrf.tools import require_aria2

_SD_RE = re.compile(r"SD:(\d+)")


def probe_seeders(torrent_path: Path | str, *, timeout_sec: int = 45) -> int:
    """Return max observed seeder count (SD). Cleans mrf-test temp always."""
    tp = Path(torrent_path)
    if not tp.is_file():
        raise FileNotFoundError(f"Torrent not found: {tp}")

    probe_dir = Path(tempfile.gettempdir()) / "mrf-test"
    kill_aria2_matching("mrf-test")
    rmtree_quiet(probe_dir)
    probe_dir.mkdir(parents=True, exist_ok=True)

    aria2 = require_aria2()
    args = [
        aria2,
        f"--dir={probe_dir}",
        "--enable-dht=true",
        "--bt-enable-lpd=true",
        f"--bt-tracker={TRACKERS_CSV}",
        "--seed-ratio=0",
        "--seed-time=0",
        f"--bt-stop-timeout={timeout_sec}",
        "--max-overall-download-limit=32K",
        "--file-allocation=none",
        "--summary-interval=5",
        "--console-log-level=notice",
        str(tp),
    ]

    try:
        _rc, output = run_with_timeout(args, timeout_sec=timeout_sec + 20)
    finally:
        kill_aria2_matching("mrf-test")
        rmtree_quiet(probe_dir)

    matches = _SD_RE.findall(output)
    return int(matches[-1]) if matches else 0
