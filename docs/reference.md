# Reference: Sources & Troubleshooting

## Source comparison

| Source | Best for | Fetch method | Common failure |
|--------|----------|--------------|----------------|
| **BTDig** | Movies and multi-file packs | itorrents.org + aria2 | No seeders (SD=0) |
| **Kemono** | Mirrored creator post attachments | API + CDN `n1`–`n4` | CDN timeout (global) |
| **Pawchive** | Kemono backup | Same path layout | `has_full: false` |
| **itorrents.org** | `.torrent` by hash | HTTP | Hash not cached |
| **TorBT** | — | **Avoid** (scam ads) | Dead swarms |
| **Forum cloud drives** | Chinese mega-packs | Manual (user) | Login/VIP required |

## aria2 peer test (60 seconds)

```bash
TRACKERS="udp://tracker.opentrackr.org:1337/announce,udp://open.stealth.si:80/announce,udp://tracker.torrent.eu.org:451/announce"
aria2c --select-file=INDEX --bt-stop-timeout=60 --summary-interval=5 \
  --enable-dht=true --bt-enable-lpd=true --bt-tracker="$TRACKERS" \
  "./torrents/HASH.torrent"
```

Or: `uv run mrf test-hash HASH`

Pick the hash with highest SD and non-zero DL.

## aria2 error: missing .aria2 control file

If files exist but resume fails (errorCode=13):
- Files likely complete → run `uv run mrf verify ./downloads --recursive`
- To re-download: delete incomplete files or add `--allow-overwrite=true` (destructive)

## Windows Explorer thumbnails missing

Raw torrent MP4s often lack `attached_pic` cover art and may have `moov` atom at file tail.

```bash
uv run mrf fix-thumbnails ./downloads --embed-cover
uv run mrf fix-thumbnails ./downloads --cache-only   # flush Explorer cache only
```

## Video compression

Use when downloaded MP4s are oversized H.264 (30–45 Mbps at 1080p). Normal 1080p only needs 8–12 Mbps.

**Default encoder:** Intel **QSV** (`--encoder qsv`) — uses CPU integrated graphics (Quick Sync), fastest option.

Output goes to `<Dir>-compressed/` by default; originals are untouched.

### Why compress?

Torrent downloads often contain H.264 at 35–45 Mbps (near-uncompressed). Re-encoding to HEVC at ~4 Mbps typically shrinks files to **10–15% of original size** with near-identical visual quality.

Real example (46 videos, 20.3 GB → ~2 GB after compression).

### Encoder comparison

Tested on **Intel Core Ultra 7 265K + RTX 5070 Ti**, sample file 181 MB / 5 min:

| Encoder | Hardware | Time | Output | % of original | Notes |
|---------|----------|------|--------|---------------|-------|
| **qsv** (default) | Intel 核顯 | **9 s** | 54 MB | 30% | Fastest, smallest files |
| **nvenc** | RTX 5070 Ti | 17 s | 86 MB | 47% | Best quality/size balance |
| **x265** | CPU | 52 s | 98 MB | 54% | Slowest, fine-tunable |
| **av1** | RTX 5070 Ti | ~15 s | ~80 MB | ~44% | Best efficiency, newer codec |

Large file test (2594 MB / 10 min):

| Encoder | Time | Output |
|---------|------|--------|
| nvenc UHQ p1 | **54 s** | 338 MB (13%) |
| x265 fast | ~3 min (est.) | ~350 MB (est.) |

Batch estimate (46 files / 20 GB):

| Encoder | Total time |
|---------|------------|
| **qsv** | **~10–15 min** |
| nvenc | ~15–30 min |
| x265 | ~1–2 hours |

### Can NPU accelerate?

**No.** The Intel NPU (AI Boost) on Core Ultra is for AI inference (Windows Studio Effects, OpenVINO models), not video encoding. Video encoding uses **QSV (iGPU)**, **NVENC (dGPU)**, or **CPU (x265)**.

### Basic usage

```bash
# Default: Intel QSV (fastest)
uv run mrf compress ./downloads --recursive

# NVIDIA GPU (better quality, slightly larger)
uv run mrf compress ./downloads --recursive --encoder nvenc

# Resume interrupted batch
uv run mrf compress ./downloads --recursive --skip-existing

# CPU encode (slowest, most control)
uv run mrf compress ./downloads --recursive --encoder x265

# AV1 via NVIDIA (RTX 40/50)
uv run mrf compress ./downloads --recursive --encoder av1

# Replace originals after verifying quality
uv run mrf compress ./downloads --recursive --replace
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DIR` | (required) | Source folder |
| `--output-dir` | `<Dir>-compressed` | Output folder |
| `--recursive` | off | Include subfolders |
| `--encoder` | `qsv` | `qsv` · `nvenc` · `av1` · `x265` |
| `--cq` | auto | Quality 28 (hevc) / 32 (av1) / CRF 20 (x265); lower = better |
| `--nv-preset` | `p1` | NVENC/AV1 speed: `p1` (fastest) … `p7` (best quality) |
| `--x265-preset` | `fast` | x265 preset when `--encoder x265` |
| `--replace` | off | Overwrite originals in place |
| `--skip-existing` | off | Skip files already in output |
| `--dry-run` | off | List files without encoding |

### Which encoder to pick?

| Goal | Use |
|------|-----|
| Fastest batch job | **`--encoder qsv`** (default) |
| Best visual quality | **`--encoder nvenc --nv-preset p7`** |
| Smallest files | **`--encoder qsv`** or **`--encoder av1`** |
| Gaming while compressing | **`--encoder qsv`** (frees dGPU) |
| Maximum quality control | **`--encoder x265 --x265-preset slow`** |

### After compression

```bash
uv run mrf verify ./downloads-compressed --recursive
uv run mrf fix-thumbnails ./downloads-compressed --recursive --embed-cover

```

Audio is copied without re-encoding (`-c:a copy`). Resolution and frame rate are preserved.

## Kemono API

```
GET https://kemono.cr/api/v1/{service}/user/{user_id}/post/{post_id}
Header: Accept: text/css
```

CDN URL pattern:
```
https://{n1|n2|n3|n4}.kemono.cr/data{path}?f={filename}
Header: Accept: text/css
Referer: https://kemono.cr/...
```

## BTDig search

Often times out. Fallback: WebSearch `"<title> btih magnet"` or user pastes hash → `uv run mrf find "..." --hash ...`.

## Trackers (public)

```
udp://tracker.opentrackr.org:1337/announce
udp://open.stealth.si:80/announce
udp://tracker.torrent.eu.org:451/announce
udp://tracker.dler.org:6969/announce
udp://exodus.desync.com:6969/announce
```

## Tools check

```bash
aria2c -v
ffprobe -version
ffmpeg -version
uv run mrf --version
```
