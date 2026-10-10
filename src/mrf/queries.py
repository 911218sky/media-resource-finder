"""Expand user request into BTDig search queries."""

from __future__ import annotations

import re

ALIASES: list[tuple[re.Pattern[str], list[str]]] = [
    (
        re.compile(r"iron\s*man\s*3|鋼鐵人\s*3", re.I),
        [
            "Iron Man 3 2013",
            "Iron Man 3 1080p",
            "Iron Man 3 BluRay",
        ],
    ),
    (
        re.compile(r"avatar\s*3|fire\s*and\s*ash", re.I),
        [
            "Avatar Fire and Ash 2025",
            "Avatar Fire and Ash 1080p",
            "Avatar 3 1080p",
        ],
    ),
    (
        re.compile(r"avatar.*fire.*ash", re.I),
        ["Avatar Fire and Ash 2025 1080p"],
    ),
]


def build_queries(query: str) -> list[str]:
    q = query.strip()
    queries: list[str] = [q]

    for pattern, aliases in ALIASES:
        if pattern.search(q):
            for a in aliases:
                if a not in queries:
                    queries.append(a)

    if re.search(r"avatar|iron\s*man|movie|1080p|2160p|4k|鋼鐵人", q, re.I) or re.search(
        r"^\S+\s+\d{4}$", q
    ):
        for suffix in ("1080p", "2160p"):
            v = f"{q} {suffix}".strip()
            if v not in queries:
                queries.append(v)

    # unique preserve order
    seen: set[str] = set()
    out: list[str] = []
    for item in queries:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
