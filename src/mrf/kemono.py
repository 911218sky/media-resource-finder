"""Kemono / Pawchive post listing and attachment download."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from mrf.paths import downloads_dir

API_BASES = ("https://kemono.cr", "https://pawchive.pw")
CDN_HOSTS = (
    "https://kemono.cr",
    "https://n1.kemono.cr",
    "https://n2.kemono.cr",
    "https://pawchive.pw",
    "https://file.pawchive.pw",
)


def fetch_post(service: str, user: str, post: str) -> dict[str, Any]:
    headers = {"Accept": "text/css"}
    last_err: Exception | None = None
    with httpx.Client(headers=headers, follow_redirects=True, timeout=30.0) as client:
        for base in API_BASES:
            url = f"{base}/api/v1/{service}/user/{user}/post/{post}"
            try:
                resp = client.get(url)
                data = resp.json()
                if data.get("title"):
                    return data
            except (httpx.HTTPError, ValueError) as exc:
                last_err = exc
    raise RuntimeError(f"Failed to fetch Kemono post: {last_err}")


def download_attachment(
    service: str,
    user: str,
    post: str,
    filename: str,
    *,
    out_dir: Path | str | None = None,
) -> Path:
    data = fetch_post(service, user, post)
    attachments = data.get("attachments") or []
    att = next((a for a in attachments if a.get("name") == filename), None)
    if not att:
        raise FileNotFoundError(f"Attachment not found: {filename}")

    dest_dir = Path(out_dir) if out_dir else downloads_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / filename
    referer = f"https://kemono.cr/{service}/user/{user}/post/{post}"
    headers = {"Accept": "text/css", "Referer": referer}

    with httpx.Client(headers=headers, follow_redirects=True, timeout=600.0) as client:
        for host in CDN_HOSTS:
            url = f"{host}/data{att['path']}?f={filename}"
            try:
                with client.stream("GET", url) as resp:
                    if resp.status_code != 200:
                        continue
                    with out.open("wb") as fh:
                        for chunk in resp.iter_bytes():
                            fh.write(chunk)
                if out.is_file() and out.stat().st_size > 0:
                    return out
            except httpx.HTTPError:
                out.unlink(missing_ok=True)

    raise RuntimeError(f"CDN unreachable. Try: mrf find \"{filename}\"")
