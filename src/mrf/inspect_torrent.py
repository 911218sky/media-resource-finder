"""Scam / malware metadata inspection (no payload download)."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from mrf.constants import AD_EXT, DANGEROUS_EXT, MEDIA_EXT, SPAM_PATTERNS
from mrf.torrent_meta import TorrentMeta, load_meta, parse_listing

Verdict = Literal["clean", "suspicious", "scam"]


@dataclass
class InspectReport:
    hash: str
    name: str
    verdict: Verdict
    score: int
    reasons: list[str] = field(default_factory=list)
    total_bytes: int = 0
    real_bytes: int = 0
    padding_bytes: int = 0
    media_count: int = 0
    media_bytes: int = 0
    dangerous_count: int = 0
    dangerous_files: list[str] = field(default_factory=list)
    media_files: list[str] = field(default_factory=list)
    file_count: int = 0
    real_file_count: int = 0

    def to_json_dict(self) -> dict[str, Any]:
        # Match PS1 key casing for last-find / agent compatibility
        d = asdict(self)
        return {
            "Hash": d["hash"],
            "Name": d["name"],
            "Verdict": d["verdict"],
            "Score": d["score"],
            "Reasons": d["reasons"],
            "TotalBytes": d["total_bytes"],
            "RealBytes": d["real_bytes"],
            "PaddingBytes": d["padding_bytes"],
            "MediaCount": d["media_count"],
            "MediaBytes": d["media_bytes"],
            "DangerousCount": d["dangerous_count"],
            "DangerousFiles": d["dangerous_files"],
            "MediaFiles": d["media_files"],
            "FileCount": d["file_count"],
            "RealFileCount": d["real_file_count"],
        }

    @property
    def exit_code(self) -> int:
        return {"clean": 0, "suspicious": 1, "scam": 2}[self.verdict]


def inspect_meta(meta: TorrentMeta) -> InspectReport:
    real = meta.real_files
    pad = meta.padding_files
    real_bytes = sum(f.size for f in real)
    pad_bytes = sum(f.size for f in pad)
    media = [f for f in real if f.ext in MEDIA_EXT]
    danger = [f for f in real if f.ext in DANGEROUS_EXT]
    media_bytes = sum(f.size for f in media)
    total = meta.total_bytes

    reasons: list[str] = []
    score = 0

    if danger:
        exts = ", ".join(sorted({f.ext for f in danger}))
        reasons.append(f"dangerous_ext: {exts} ({len(danger)} file(s))")
        score += 50
        if media:
            reasons.append(
                "mixed_malware_with_media: video present but also dangerous files; refuse whole torrent"
            )
            score += 20

    blob = "\n".join([meta.name] + [f.path for f in real])
    for pat in SPAM_PATTERNS:
        if pat and pat in blob:
            reasons.append(f"spam_name: {pat}")
            score += 25
            break

    if len(pad) >= 3 and real:
        pad_ratio = (pad_bytes / total) if total > 0 else 0.0
        if pad_ratio >= 0.5 or (media_bytes == 0 and pad_bytes > real_bytes):
            p_mb = round(pad_bytes / (1024 * 1024), 1)
            r_mb = round(real_bytes / (1024 * 1024), 1)
            reasons.append(f"bitcomet_padding_heavy: pad={p_mb}MB real={r_mb}MB")
            score += 30

    if not media:
        reasons.append("no_media_files")
        score += 35
    elif total > 0 and media_bytes > 0 and (media_bytes / total) < 0.05:
        m_mb = round(media_bytes / (1024 * 1024), 1)
        t_gb = round(total / (1024**3), 2)
        reasons.append(f"tiny_media_vs_total: media={m_mb}MB / total={t_gb}GB")
        score += 25

    if total >= 100 * 1024 * 1024 and 0 < real_bytes < 5 * 1024 * 1024 and not media:
        t_gb = round(total / (1024**3), 2)
        r_kb = round(real_bytes / 1024)
        reasons.append(f"fake_size: advertised {t_gb}GB but real non-pad ~{r_kb}KB")
        score += 40

    ads = [
        f
        for f in real
        if f.ext in AD_EXT or (f.ext == ".png" and f.size < 50 * 1024)
    ]
    if not media and len(ads) >= 2 and len(ads) >= math.ceil(len(real) * 0.4):
        reasons.append(f"ad_landing_files: {len(ads)}")
        score += 20

    if score >= 50:
        verdict: Verdict = "scam"
    elif score >= 25:
        verdict = "suspicious"
    else:
        verdict = "clean"

    return InspectReport(
        hash=meta.hash,
        name=meta.name,
        verdict=verdict,
        score=score,
        reasons=reasons,
        total_bytes=total,
        real_bytes=real_bytes,
        padding_bytes=pad_bytes,
        media_count=len(media),
        media_bytes=media_bytes,
        dangerous_count=len(danger),
        dangerous_files=[f.path for f in danger],
        media_files=[
            f"{f.path} ({round(f.size / (1024 * 1024), 1)}MB)" for f in media
        ],
        file_count=len(meta.files),
        real_file_count=len(real),
    )


def inspect_torrent(torrent_path: Path | str) -> InspectReport:
    return inspect_meta(load_meta(torrent_path))


def inspect_listing(listing: str) -> InspectReport:
    """Inspect from pre-captured aria2c -S text (for tests)."""
    return inspect_meta(parse_listing(listing))
