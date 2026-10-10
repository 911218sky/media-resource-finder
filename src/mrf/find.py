"""Search BTDig, inspect, probe seeders, write last-find.json."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

import httpx

from mrf.constants import BTDIG_SEARCH, USER_AGENT
from mrf.fetch import fetch_torrent
from mrf.hashutil import try_normalize_hash
from mrf.inspect_torrent import inspect_torrent
from mrf.paths import last_find_path, project_root, torrents_dir
from mrf.probe import probe_seeders
from mrf.queries import build_queries


_BTIH = re.compile(r"btih:([a-f0-9]{40})", re.I)


@dataclass
class FindResult:
    hash: str
    seeders: int
    status: str
    name: str
    verdict: str = "unknown"
    score: int = -1
    reasons: list[str] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "Hash": self.hash,
            "Seeders": self.seeders,
            "Status": self.status,
            "Name": self.name,
            "Verdict": self.verdict,
            "Score": self.score,
            "Reasons": self.reasons,
        }


def search_btdig(query: str, *, timeout: float = 20.0) -> list[str]:
    url = BTDIG_SEARCH.format(query=quote(query))
    try:
        with httpx.Client(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return []
            return [m.group(1).lower() for m in _BTIH.finditer(resp.text)]
    except httpx.HTTPError:
        return []


def find(
    query: str,
    *,
    hashes: list[str] | None = None,
    skip_test: bool = False,
    test_seconds: int = 45,
    max_test: int = 5,
) -> list[FindResult]:
    root = project_root()
    tdir = torrents_dir(root)

    all_hashes: list[str] = []
    seen: set[str] = set()
    for h in hashes or []:
        clean = try_normalize_hash(h)
        if clean and clean not in seen:
            seen.add(clean)
            all_hashes.append(clean)

    queries = build_queries(query)
    search_urls: list[str] = []
    for search_q in queries:
        url = BTDIG_SEARCH.format(query=quote(search_q))
        search_urls.append(url)
        found = search_btdig(search_q)
        for h in found:
            if h not in seen:
                seen.add(h)
                all_hashes.append(h)

    if not all_hashes:
        # stash hint URLs for CLI
        raise LookupError(
            "No hashes from BTDig. Try WebSearch for btih, or pass --hash. "
            f"First URL: {search_urls[0] if search_urls else ''}"
        )

    results: list[FindResult] = []
    limit = min(max_test, len(all_hashes))
    for i, h in enumerate(all_hashes[:limit]):
        try:
            tp = fetch_torrent(h, out_dir=tdir, magnet_timeout=90)
        except Exception:
            results.append(
                FindResult(hash=h, seeders=0, status="no_torrent", name="?")
            )
            continue

        if not tp.is_file() or tp.stat().st_size < 500:
            results.append(
                FindResult(hash=h, seeders=0, status="no_torrent", name="?")
            )
            continue

        try:
            insp = inspect_torrent(tp)
        except Exception as exc:
            results.append(
                FindResult(
                    hash=h,
                    seeders=0,
                    status="inspect_error",
                    name="?",
                    reasons=[str(exc)],
                )
            )
            continue

        name = insp.name if insp.name != "?" else "unknown"
        if insp.verdict == "scam":
            tp.unlink(missing_ok=True)
            results.append(
                FindResult(
                    hash=h,
                    seeders=0,
                    status="scam",
                    name=name,
                    verdict=insp.verdict,
                    score=insp.score,
                    reasons=list(insp.reasons),
                )
            )
            continue

        if skip_test:
            results.append(
                FindResult(
                    hash=h,
                    seeders=-1,
                    status="skipped",
                    name=name,
                    verdict=insp.verdict,
                    score=insp.score,
                    reasons=list(insp.reasons),
                )
            )
            continue

        try:
            sd = probe_seeders(tp, timeout_sec=test_seconds)
        except Exception:
            sd = 0

        status = "alive" if sd >= 1 else "dead"
        if insp.verdict == "suspicious" and status == "alive":
            status = "suspicious"

        results.append(
            FindResult(
                hash=h,
                seeders=sd,
                status=status,
                name=name,
                verdict=insp.verdict,
                score=insp.score,
                reasons=list(insp.reasons),
            )
        )

    report_path = last_find_path(root)
    report_path.write_text(
        json.dumps([r.to_json_dict() for r in results], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return results


def pick_best(results: list[FindResult]) -> FindResult | None:
    alive = sorted(
        [r for r in results if r.status == "alive"],
        key=lambda r: r.seeders,
        reverse=True,
    )
    if alive:
        return alive[0]
    sus = sorted(
        [r for r in results if r.status == "suspicious"],
        key=lambda r: r.seeders,
        reverse=True,
    )
    if sus:
        return sus[0]
    if not results:
        return None
    return max(results, key=lambda r: r.seeders)
