"""Fetch .torrent via HTTP cache or magnet metadata."""

from __future__ import annotations

from pathlib import Path

import httpx


from mrf.constants import TORRENT_CACHE_URLS, TRACKERS_CSV, USER_AGENT
from mrf.hashutil import normalize_hash
from mrf.paths import torrents_dir
from mrf.process_util import kill_aria2_matching, run_with_timeout, unlink_quiet
from mrf.tools import require_aria2


def fetch_torrent(
    hash_value: str,
    *,
    out_dir: Path | None = None,
    magnet_timeout: int = 120,
) -> Path:
    h = normalize_hash(hash_value)
    dest_dir = out_dir or torrents_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / f"{h}.torrent"

    if out.is_file() and out.stat().st_size > 1000:
        return out

    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(headers=headers, follow_redirects=True, timeout=20.0) as client:
        for template in TORRENT_CACHE_URLS:
            url = template.format(hash=h)
            try:
                resp = client.get(url)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    out.write_bytes(resp.content)
                    return out
            except httpx.HTTPError:
                pass
            unlink_quiet(out)

    # Magnet metadata fallback via aria2
    aria2 = require_aria2()
    args = [
        aria2,
        "--bt-metadata-only=true",
        f"--bt-stop-timeout={magnet_timeout}",
        "--enable-dht=true",
        "--bt-enable-lpd=true",
        f"--bt-tracker={TRACKERS_CSV}",
        f"--dir={dest_dir}",
        f"magnet:?xt=urn:btih:{h}",
    ]
    run_with_timeout(args, timeout_sec=magnet_timeout + 30)
    kill_aria2_matching(h, "bt-metadata-only")

    if out.is_file() and out.stat().st_size > 1000:
        return out

    # aria2 may write a differently named .torrent
    candidates = sorted(
        [p for p in dest_dir.glob("*.torrent") if p.stat().st_size > 1000],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        found = candidates[0]
        if found.resolve() != out.resolve():
            found.replace(out)
        return out

    raise RuntimeError(f"Failed to get .torrent for {h}")
