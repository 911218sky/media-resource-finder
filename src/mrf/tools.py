"""Locate external CLI tools (aria2c, ffmpeg, ffprobe, curl)."""

from __future__ import annotations

import shutil
from functools import lru_cache


@lru_cache(maxsize=16)
def which(name: str) -> str | None:
    return shutil.which(name)


def require(name: str, install_hint: str) -> str:
    path = which(name)
    if not path:
        raise RuntimeError(f"{name} not found. {install_hint}")
    return path


def require_aria2() -> str:
    return require(
        "aria2c",
        "Install: Windows `winget install aria2` | macOS `brew install aria2` | Linux `sudo apt install aria2`",
    )


def require_ffprobe() -> str:
    return require(
        "ffprobe",
        "Install ffmpeg: Windows `winget install yt-dlp.FFmpeg` | macOS `brew install ffmpeg` | Linux `sudo apt install ffmpeg`",
    )


def require_ffmpeg() -> str:
    return require(
        "ffmpeg",
        "Install ffmpeg: Windows `winget install yt-dlp.FFmpeg` | macOS `brew install ffmpeg` | Linux `sudo apt install ffmpeg`",
    )
