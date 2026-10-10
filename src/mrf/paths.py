"""Project root and runtime directories."""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """Repo root (directory with pyproject.toml / downloads / torrents)."""
    # src/mrf/paths.py -> parents: mrf, src, repo
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file() and (parent / "src" / "mrf").is_dir():
            return parent
        if (parent / "torrents").is_dir() and (parent / "downloads").is_dir():
            return parent
    return here.parents[2]


def torrents_dir(root: Path | None = None) -> Path:
    d = (root or project_root()) / "torrents"
    d.mkdir(parents=True, exist_ok=True)
    return d


def downloads_dir(root: Path | None = None) -> Path:
    d = (root or project_root()) / "downloads"
    d.mkdir(parents=True, exist_ok=True)
    return d


def last_find_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "last-find.json"
