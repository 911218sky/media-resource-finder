"""HEVC / AV1 re-encode via ffmpeg."""

from __future__ import annotations

import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from mrf.tools import require_ffmpeg, require_ffprobe

Encoder = Literal["qsv", "nvenc", "av1", "x265"]


@dataclass
class CompressSummary:
    done: int = 0
    failed: list[str] = field(default_factory=list)
    saved_bytes: int = 0
    total_in: int = 0
    output_dir: Path | None = None


def _ffprobe_field(path: Path, *extra: str) -> str:
    ffprobe = require_ffprobe()
    proc = subprocess.run(
        [ffprobe, "-v", "error", *extra, str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return (proc.stdout or "").strip()


def has_attached_pic(path: Path) -> bool:
    return bool(
        _ffprobe_field(
            path,
            "-select_streams",
            "v:1",
            "-show_entries",
            "stream=codec_name",
            "-of",
            "csv=p=0",
        )
    )


def video_codec(path: Path) -> str:
    return _ffprobe_field(
        path,
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name",
        "-of",
        "csv=p=0",
    )


def _encode_args(
    encoder: Encoder,
    quality: int,
    *,
    nv_preset: str,
    x265_preset: str,
    has_cover: bool,
) -> list[str]:
    vlabel = ":0" if has_cover else ""
    if encoder == "nvenc":
        tag = ["-tag:v:0", "hvc1"] if has_cover else ["-tag:v", "hvc1"]
        a = [
            f"-c:v{vlabel}",
            "hevc_nvenc",
            "-preset",
            nv_preset,
            "-tune",
            "uhq",
            "-rc",
            "vbr",
            "-cq:v",
            str(quality),
            "-b:v",
            "0",
            *tag,
        ]
    elif encoder == "av1":
        a = [
            f"-c:v{vlabel}",
            "av1_nvenc",
            "-preset",
            nv_preset,
            "-tune",
            "uhq",
            "-rc",
            "vbr",
            "-cq:v",
            str(quality),
            "-b:v",
            "0",
        ]
    else:  # x265
        a = [
            f"-c:v{vlabel}",
            "libx265",
            "-crf",
            str(quality),
            "-preset",
            x265_preset,
            "-tag:v",
            "hvc1",
        ]
    if has_cover:
        a += ["-c:v:1", "copy", "-disposition:v:1", "attached_pic"]
    return a


def compress_dir(
    directory: Path | str,
    *,
    output_dir: Path | str | None = None,
    recursive: bool = False,
    encoder: Encoder = "qsv",
    cq: int = 0,
    nv_preset: str = "p1",
    x265_preset: str = "fast",
    replace: bool = False,
    dry_run: bool = False,
    skip_existing: bool = False,
) -> CompressSummary:
    src_root = Path(directory).resolve()
    if not src_root.is_dir():
        raise FileNotFoundError(f"Directory not found: {src_root}")
    require_ffmpeg()

    if cq == 0:
        cq = {"av1": 32, "x265": 20}.get(encoder, 28)

    if output_dir:
        out_root = Path(output_dir)
    else:
        out_root = src_root.parent / f"{src_root.name}-compressed"

    if not dry_run and not replace:
        out_root.mkdir(parents=True, exist_ok=True)

    pattern = "**/*.mp4" if recursive else "*.mp4"
    files = sorted(src_root.glob(pattern), key=lambda p: p.stat().st_size, reverse=True)
    summary = CompressSummary(total_in=sum(f.stat().st_size for f in files), output_dir=None if replace else out_root)

    for file in files:
        rel = file.relative_to(src_root)
        dest = file if replace else out_root / rel
        if skip_existing and dest.is_file() and dest.stat().st_size > 1024 * 1024:
            continue

        src_codec = video_codec(file)
        if src_codec in {"hevc", "av1"} and encoder != "x265":
            if not replace and not dest.exists() and not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(file.read_bytes())
            continue

        if dry_run:
            summary.done += 1
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.parent / f".compress-{uuid.uuid4().hex}.mp4"
        cover = has_attached_pic(file)
        ffmpeg = require_ffmpeg()

        if encoder == "qsv":
            args = [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-stats",
                "-init_hw_device",
                "qsv=qs",
                "-filter_hw_device",
                "qs",
                "-i",
                str(file),
            ]
            if cover:
                args += [
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a?",
                    "-map",
                    "0:v:1",
                    "-filter:v:0",
                    "format=nv12,hwupload=extra_hw_frames=64",
                    "-c:v:0",
                    "hevc_qsv",
                    "-global_quality",
                    str(cq),
                    "-c:a",
                    "copy",
                    "-c:v:1",
                    "copy",
                    "-disposition:v:1",
                    "attached_pic",
                    "-movflags",
                    "+faststart",
                    str(tmp),
                ]
            else:
                args += [
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a?",
                    "-vf",
                    "format=nv12,hwupload=extra_hw_frames=64",
                    "-c:v",
                    "hevc_qsv",
                    "-global_quality",
                    str(cq),
                    "-c:a",
                    "copy",
                    "-movflags",
                    "+faststart",
                    str(tmp),
                ]
        else:
            args = [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-stats",
                "-i",
                str(file),
            ]
            if cover:
                args += ["-map", "0:v:0", "-map", "0:a?", "-map", "0:v:1"]
            else:
                args += ["-map", "0:v:0", "-map", "0:a?"]
            args += _encode_args(
                encoder, cq, nv_preset=nv_preset, x265_preset=x265_preset, has_cover=cover
            )
            args += ["-c:a", "copy", "-movflags", "+faststart", str(tmp)]

        t0 = time.perf_counter()
        proc = subprocess.run(args, check=False)
        _ = time.perf_counter() - t0
        if proc.returncode != 0 or not tmp.is_file():
            summary.failed.append(str(rel))
            tmp.unlink(missing_ok=True)
            continue

        size_out = tmp.stat().st_size
        summary.saved_bytes += file.stat().st_size - size_out
        tmp.replace(dest)
        summary.done += 1

    return summary
