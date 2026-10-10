# Media Resource Finder

Cross-platform toolkit to find and download videos via BTDig torrents, magnet/DHT, Kemono mirrors, and aria2.

**For AI agents:** [`docs/AGENTS.md`](docs/AGENTS.md)  
**For humans:** this file · [`docs/`](docs/)

Runs on **Windows / macOS / Linux** via Python + [uv](https://docs.astral.sh/uv/).

---

## Workflow in one line

```
mrf find  →  mrf download  →  mrf verify
 find hash    download         verify playable
```

Optional: `mrf fix-thumbnails` (Windows) · `mrf compress`

---

## Prerequisites (one-time)

### 1. Install uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install system tools

| Tool | Windows | macOS | Linux (Debian/Ubuntu) |
|------|---------|-------|------------------------|
| **aria2** | `winget install aria2` | `brew install aria2` | `sudo apt install aria2` |
| **ffmpeg** (ffprobe) | `winget install yt-dlp.FFmpeg` | `brew install ffmpeg` | `sudo apt install ffmpeg` |

Check:

```bash
aria2c -v
ffprobe -version
```

### 3. Install this project

```bash
cd media-resource-finder
uv sync
```

---

## Quick start

```bash
cd <project-root>   # folder with pyproject.toml

# 1. Search + test seeders
uv run mrf find "Iron Man 3"

# 2. Download (find prints the recommended hash)
uv run mrf download <40-char-hash>

# 3. Verify
uv run mrf verify ./downloads --recursive
```

---

## Example: find "Iron Man 3"

Official title: **Iron Man 3 (2013)** · also works with `鋼鐵人3`

```bash
uv run mrf find "Iron Man 3"
uv run mrf find "鋼鐵人3"
uv run mrf download <40-char-hash>
uv run mrf verify ./downloads --recursive
```

See `examples/iron-man-3.json`.

---

## Example: find "Avatar 3"

Official title: **Avatar: Fire and Ash (2025)**

```bash
uv run mrf find "Avatar 3"
uv run mrf download <40-char-hash>
uv run mrf verify ./downloads --recursive
```

See `examples/avatar-fire-and-ash.json`.

---

## Example: compress oversized videos

```bash
# Default: Intel QSV iGPU (fastest on Windows Intel)
uv run mrf compress ./downloads --recursive

# NVIDIA GPU
uv run mrf compress ./downloads --recursive --encoder nvenc

# Resume if interrupted
uv run mrf compress ./downloads --recursive --skip-existing
```

| Encoder | Hardware | Best for |
|---------|----------|----------|
| **qsv** (default) | Intel iGPU | Fastest |
| nvenc | NVIDIA GPU | Quality |
| x265 | CPU | Max control |
| av1 | NVIDIA (40/50) | Efficiency |

Details: [`docs/reference.md`](docs/reference.md#video-compression)

---

## Commands

| Command | Purpose | When |
|---------|---------|------|
| **`mrf find`** | Search + inspect + probe seeders | **Always first** |
| **`mrf download`** | aria2 download | After find finds seeders |
| **`mrf verify`** | Check mp4 integrity | After download |
| **`mrf inspect`** | Scam/malware metadata check | Manual review |
| **`mrf compress`** | HEVC/AV1 re-encode | Files too large |
| **`mrf fix-thumbnails`** | Explorer thumbnails | Windows only |
| **`mrf kemono`** | Kemono post attachments | Patreon mirrors |
| `mrf test-hash` | Probe one hash | Manual re-check |
| `mrf fetch-torrent` | Get `.torrent` file | Advanced |
| `mrf queries` | Show expanded search queries | Debug aliases |

```bash
uv run mrf --help
uv run mrf find --help
```

---

## What find can and cannot do

| Can | Cannot |
|-----|--------|
| Expand queries (e.g. Iron Man 3 → 2013 / 1080p) | Guarantee BTDig works |
| Merge hashes from multiple searches | Guarantee every hash has seeders |
| Auto-inspect + test top 5 hashes | Find Kemono-only files |
| Print next steps when search fails | Replace legal streaming |

**Need seeders (SD ≥ 1) to download.** Results saved to `last-find.json`.

---

## Source selection

| Content | Approach |
|---------|----------|
| Movies / collections | find → download |
| Kemono post | `mrf kemono` |
| Kemono CDN down | find by filename |
| BT dead swarm | try another hash / wait |

**Do not use TorBT** (scam notifications).

---

## Download behavior

- **No disk pre-allocation** — file size grows as data arrives
- **No upload by default** (`--seed-ratio 0`)
- **Scam gate** — refuses junk/malware torrents unless `--force`

Output folder: `downloads/`

---

## Documentation

| File | Purpose |
|------|---------|
| `README.md` | Human quickstart (this file) |
| `docs/AGENTS.md` | AI agent workflow |
| `docs/reference.md` | Troubleshooting + compression |
| `docs/examples.md` | Case study walkthroughs |
| `AGENTS.md` | Short pointer to `docs/AGENTS.md` |

---

## Folder layout

```
media-resource-finder/
├── pyproject.toml      ← uv / Python package
├── uv.lock
├── README.md
├── AGENTS.md           ← pointer → docs/AGENTS.md
├── docs/               ← human + agent guides
├── src/mrf/            ← Python toolkit
├── tests/
├── examples/           ← JSON case data
├── torrents/           ← runtime (gitignored)
├── downloads/          ← output (gitignored)
└── last-find.json      ← latest search report (gitignored)
```


---

## Develop / test

```bash
uv sync
uv run pytest
uv run mrf --version
```
