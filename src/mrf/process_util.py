"""Cross-platform process helpers for aria2 probe/metadata cleanup."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

import psutil


def kill_aria2_matching(*needles: str) -> int:
    """Kill aria2/aria2c processes whose cmdline contains all needles. Returns count."""
    killed = 0
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if "aria2" not in name:
                continue
            cmdline = " ".join(proc.info.get("cmdline") or [])
            if all(n in cmdline for n in needles):
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return killed


def run_with_timeout(
    args: list[str],
    *,
    timeout_sec: float,
    cwd: Path | str | None = None,
) -> tuple[int, str]:
    """Run process; on timeout kill it and any matching leftovers. Returns (rc, combined output)."""
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd) if cwd else None,
    )
    try:
        out, err = proc.communicate(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            out, err = "", ""
            try:
                os.kill(proc.pid, signal.SIGKILL)
            except OSError:
                pass
    combined = (out or "") + (err or "")
    return proc.returncode if proc.returncode is not None else -1, combined


def rmtree_quiet(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def unlink_quiet(*paths: Path) -> None:
    for p in paths:
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass


def sleep_brief(sec: float = 0.2) -> None:
    time.sleep(sec)
