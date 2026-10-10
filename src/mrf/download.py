"""Download via aria2 with inspect gate."""

from __future__ import annotations

import subprocess
from pathlib import Path

from mrf.constants import TRACKERS_CSV
from mrf.fetch import fetch_torrent
from mrf.hashutil import normalize_hash
from mrf.inspect_torrent import inspect_torrent
from mrf.paths import downloads_dir, torrents_dir
from mrf.tools import require_aria2
from mrf.torrent_meta import load_meta, media_file_indices


def download(
    hash_value: str,
    *,
    output_dir: Path | str | None = None,
    select_file: list[int] | None = None,
    videos_only: bool = False,
    force: bool = False,
    seed_ratio: float = 0.0,
    seed_time: int = 0,
) -> Path:
    h = normalize_hash(hash_value)
    out = Path(output_dir) if output_dir else downloads_dir()
    out.mkdir(parents=True, exist_ok=True)
    tdir = torrents_dir()

    torrent_path = fetch_torrent(h, out_dir=tdir)
    if torrent_path.stat().st_size < 1000:
        raise RuntimeError(f"Cannot get .torrent for hash {h}")

    report = inspect_torrent(torrent_path)
    if report.verdict == "scam":
        if not force:
            torrent_path.unlink(missing_ok=True)
            raise RuntimeError(
                f"REFUSED: inspect marked SCAM (score={report.score}): "
                + "; ".join(report.reasons)
            )
    elif report.verdict == "suspicious" and not force:
        raise RuntimeError(
            f"REFUSED: torrent is SUSPICIOUS (use --force after review): "
            + "; ".join(report.reasons)
        )

    aria2 = require_aria2()
    log_path = tdir / f"download-{h}.log"
    args = [
        aria2,
        f"--dir={out}",
        "--file-allocation=none",
        "--bt-prioritize-piece=head",
        "--split=16",
        "--max-connection-per-server=16",
        "--bt-max-peers=500",
        "--enable-dht=true",
        "--bt-enable-lpd=true",
        f"--bt-tracker={TRACKERS_CSV}",
        f"--seed-ratio={seed_ratio}",
        f"--seed-time={seed_time}",
        "--continue=true",
        "--summary-interval=30",
        "--console-log-level=notice",
        f"--log={log_path}",
        str(torrent_path),
    ]

    indices = list(select_file or [])
    if not indices and videos_only:
        meta = load_meta(torrent_path)
        indices = media_file_indices(meta, videos_only_mp4=True)
        if not indices:
            raise RuntimeError("No mp4 files found in torrent.")

    if indices:
        args = [f"--select-file={','.join(str(i) for i in indices)}"] + args

    proc = subprocess.run(args, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"aria2 exited with code {proc.returncode}")
    return out
