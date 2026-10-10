"""Info-hash normalization."""

from __future__ import annotations

import re


def normalize_hash(value: str) -> str:
    """Return lowercase 40-char hex info-hash or raise ValueError."""
    s = value.strip().lower()
    if "btih:" in s:
        s = s.split("btih:", 1)[1]
    s = re.sub(r"[^a-f0-9].*$", "", s)
    if len(s) != 40:
        raise ValueError(f"Hash must be 40 hex characters (got length {len(s)})")
    return s


def try_normalize_hash(value: str) -> str | None:
    try:
        return normalize_hash(value)
    except ValueError:
        return None
