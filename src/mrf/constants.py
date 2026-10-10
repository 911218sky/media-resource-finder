"""Shared constants: trackers, extensions, spam name patterns."""

from __future__ import annotations

TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://tracker.dler.org:6969/announce",
    "udp://exodus.desync.com:6969/announce",
]

TRACKERS_CSV = ",".join(TRACKERS)

DANGEROUS_EXT = frozenset(
    {
        ".exe",
        ".scr",
        ".bat",
        ".cmd",
        ".com",
        ".pif",
        ".msi",
        ".msp",
        ".vbs",
        ".vbe",
        ".js",
        ".jse",
        ".wsf",
        ".wsh",
        ".ps1",
        ".psm1",
        ".lnk",
        ".hta",
        ".cpl",
        ".jar",
        ".reg",
        ".dll",
        ".sys",
        ".chm",
        ".hlp",
        ".msc",
        ".iso",
        ".img",
        ".apk",
    }
)

MEDIA_EXT = frozenset(
    {
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".wmv",
        ".m4v",
        ".webm",
        ".flv",
        ".ts",
        ".m2ts",
        ".mpg",
        ".mpeg",
        ".vob",
        ".rmvb",
        ".3gp",
    }
)

AD_EXT = frozenset({".html", ".htm", ".mht", ".url", ".txt"})


def _u(*codes: int) -> str:
    return "".join(chr(c) for c in codes)


# Escort / fake-app spam magnets (codepoints = encoding-safe)
SPAM_PATTERNS: tuple[str, ...] = (
    _u(0x7EA6, 0x70AE),
    _u(0x7D04, 0x70AE),
    _u(0x5916, 0x56F4),
    _u(0x5916, 0x570D),
    _u(0x4E00, 0x952E, 0x7EA6),
    _u(0x4E00, 0x9375, 0x7D04),
    _u(0x542B, 0x7F9E, 0x8349),
    _u(0x5979, 0x8DA3),
    _u(0x798F, 0x5229, 0x5E73, 0x53F0),
    _u(0x534E, 0x4EBA, 0x7B2C, 0x4E00),
    _u(0x83EF, 0x4EBA, 0x7B2C, 0x4E00),
    _u(0x5168, 0x56FD, 0x5916, 0x56F4),
    _u(0x5168, 0x570B, 0x5916, 0x570D),
    "91" + _u(0x7EA6),
    "91" + _u(0x7D04),
    _u(0x540C, 0x57CE, 0x7EA6),
    _u(0x540C, 0x57CE, 0x7D04),
    _u(0x4EA4, 0x53CB) + "app",
    _u(0x4EA4, 0x53CB) + "APP",
    _u(0x7834, 0x89E3, 0x7248),
    _u(0x52A0, 0x5FAE),
    _u(0x542B, 0x7F9E, 0x8349, 0x0041, 0x0050, 0x0050),
)

BTDIG_SEARCH = "https://en.btdig.com/search?q={query}"
TORRENT_CACHE_URLS = (
    "https://itorrents.org/torrent/{hash}.torrent",
    "https://btcache.me/torrent/{hash}",
)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
