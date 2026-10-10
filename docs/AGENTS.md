# Agent Guide

When user asks to **find / download a video, movie, or media file**, follow this guide.

**Project root:** directory containing `pyproject.toml` (run all commands from here).

**CLI:** `uv run mrf <command>` (Python package; requires `uv sync` once).

---

## Mandatory workflow

```
[1] Classify request
[2] Run: uv run mrf find "..."
[3] Test hash seeders (find does this)
[4] uv run mrf download <best-hash>
[5] uv run mrf verify ./downloads --recursive
[6] mrf fix-thumbnails if Explorer shows generic icons (Windows)
[7] mrf compress if user wants smaller files (optional)
```

### Step 1 — Classify

| Type | Examples | Primary source |
|------|----------|----------------|
| **Movie** | Iron Man 3, Avatar 3 | BTDig + hash test |
| **Kemono post** | user/post ID | kemono → BTDig fallback |
| **Multi-file pack** | trilogy / season pack | Known hash or BTDig |
| **Single file in torrent** | one mp4 from pack | `mrf download HASH -s N` |

### Step 2 — Find (always run first)

```bash
cd <project-root>
uv run mrf find "<user words>"
```

- Query aliases expand automatically (e.g. Iron Man 3 / 鋼鐵人3 → 2013 / 1080p)
- BTDig HTTP **often times out** → use **WebSearch** for `"<title> btih magnet"` and pass hash
- If user or WebSearch provides hash: `uv run mrf find "..." --hash abc...`

**Never use TorBT** (scam notifications).

### Step 3 — Pick hash

- **SD >= 1** required to download
- Prefer **1080p** unless user wants 4K (smaller, faster)
- Same movie may have many hashes — test top 3–5
- Read `last-find.json` after find
- **Skip Status=`scam`** — junk/malware magnets (`.chm`/`.exe`, escort spam names, BitComet padding fakes). Find deletes their cache.
- **Status=`suspicious`** — warn user; only `mrf download ... --force` if they insist after review

### Step 4 — Download

```bash
uv run mrf download <40-char>                 # all files
uv run mrf download <hash> --videos-only      # mp4 only
uv run mrf download <hash> -s 118             # one file (aria2 index)
```

- Uses `--file-allocation=none` (size grows = progress)
- Output: `downloads/`

### Step 5 — Verify

```bash
uv run mrf verify ./downloads --recursive
```

### Step 6 — Thumbnails (optional, Windows)

```bash
uv run mrf fix-thumbnails ./downloads --embed-cover
```

---

## Agent capability tiers

| Tier | Tools available | Best search strategy |
|------|-----------------|----------------------|
| **A — Full** | Shell + WebSearch | mrf find → WebSearch fallback → test-hash |
| **B — Shell only** | Terminal, aria2 | mrf find → ask user to paste hash |
| **C — Read-only / Ask** | No shell | Read `examples/*.json`, tell user exact commands |

**Always run on the user's machine** (not a sandbox without network).

---

## Decision tree

```
User wants media
  |
  v
Has Kemono user/post ID? ----YES----> mrf kemono
  |                                    |
  NO                                   CDN failed?
  |                                    |
  v                                    v
uv run mrf find "..."              mrf find by filename
  |
  v
Got hash(es) with SD>=1?
  |
  v
inspect (auto) ----scam----> delete cache, try next hash
  |
  clean / suspicious
  |
  v
mrf download (refuse scam; suspicious needs --force)
  |
  no clean alive?
  v
  +-------+-------+
  |               |
WebSearch       Ask user
(if avail)      paste hash
```

---

## Method 1: mrf find (default)

```bash
cd <project-root>
uv run mrf find "<user request>"
```

**Does:**
1. Expands query aliases
2. Tries BTDig via HTTP
3. Runs inspect on each `.torrent` (scam gate before probe)
4. Tests up to 5 non-scam hashes for seeders
5. Writes `last-find.json` + prints recommended `mrf download` command

**Agent action:** Read `last-find.json` after run. Prefer `Status=alive` + `Verdict=clean`. Never download `Status=scam`. If exit code 1, go to Method 2.

---

## Method 2: WebSearch (when BTDig fails or no seeders)

**Do NOT open** TorBT, random torrent index sites, or scam pages.

### Query templates

| Goal | WebSearch query |
|------|-----------------|
| Movie hash | `"<Official Title>" 1080p btih magnet` |
| Movie hash (alt) | `"<Title>" <year> infohash torrent` |
| Creator pack | `"<Creator>" <filename> btih` |
| Verify hash | `"<40-char hash>" torrent seeders` |
| Official title | `"<colloquial name>" official movie title year` |

### After WebSearch

```bash
uv run mrf find "Iron Man 3" --hash <40-char-hash>
# or
uv run mrf test-hash <40-char-hash>
```

**Agent must:** Validate hash is exactly 40 hex chars. Never trust executable download links.

---

## Method 3: Kemono API

```bash
uv run mrf kemono --user <id> --post <id>                 # list
uv run mrf kemono --user <id> --post <id> --file x.mp4    # download
```

**If CDN fails:** Switch to Method 1 or 2 with filename + creator name.

---

## Method 4: Known examples (fast path)

Check `examples/` before searching:

| File | Use case |
|------|----------|
| `iron-man-3.json` | Iron Man 3 / 鋼鐵人3 |
| `avatar-fire-and-ash.json` | Avatar 3 / Fire and Ash |

Re-test seeders every time — hashes go dead.

---

## Content type × recommended flow

| Content | Step 1 | Step 2 if fail | Step 3 |
|---------|--------|----------------|--------|
| **Hollywood movie** | mrf find | WebSearch btih | test multiple hashes |
| **Kemono post** | mrf kemono | mrf find by filename | WebSearch title + file |
| **Multi-file pack** | examples/ or find | WebSearch btih | test-hash each candidate |
| **Single file in pack** | find hash for pack | aria2c -S / inspect | `mrf download HASH -s N` |

---

## Command map

| Command | Role |
|---------|------|
| **`mrf find`** | START HERE — search + inspect + test hashes |
| `mrf queries` | Query expansion (debug) |
| `mrf fetch-torrent` | .torrent from cache or magnet |
| **`mrf inspect`** | Scam/malware metadata check (no download) |
| `mrf test-hash` | Quick seeder check only |
| **`mrf download`** | aria2 download (refuses scam unless `--force`) |
| **`mrf verify`** | ffprobe check |
| `mrf fix-thumbnails` | Explorer video thumbnails (Windows) |
| `mrf compress` | HEVC re-encode (qsv/nvenc/x265/av1) |
| `mrf kemono` | Kemono/Pawchive posts |

---

## Per-agent playbooks

### Cursor Agent (Tier A — full tools)

1. `uv run mrf find "..."`
2. If no seeders: WebSearch `"title btih 1080p"`
3. `uv run mrf test-hash` on top candidates
4. `uv run mrf download` when user asked to download
5. `uv run mrf verify` when complete
6. `uv run mrf fix-thumbnails` if user reports missing thumbnails

### Agent with shell only (Tier B)

1. `uv run mrf find "..."`
2. If search fails: tell user to paste a 40-char hash
3. `uv run mrf find "..." --hash <pasted>`
4. Print `mrf download` command for user to run

### Agent without shell (Tier C)

1. Read `examples/*.json` and `last-find.json` if exists
2. Output exact `uv run mrf ...` commands for user
3. Explain: need SD ≥ 1, file size grows in `downloads/`

---

## WebSearch vs BTDig

| Tool | Strength | Weakness |
|------|----------|----------|
| **mrf find (BTDig HTTP)** | Automated, tests seeders | Often times out |
| **WebSearch** | Finds hashes when BTDig blocked | May return scam sites — extract hash only |
| **User paste hash** | Works when automated search fails | Needs user to provide hash |

**Combine them:** find first → WebSearch → user paste hash.

---

## Safety rules (all agents)

- **Never** open TorBT or scam torrent index sites
- **Never** run `.exe` / `.chm` / `.scr` / `.bat` from torrents
- **Never** commit `.torrent`, logs, or `downloads/` to git
- **Do** mention legal streaming for major studio films
- **Do** report honestly: SD=0 means dead, CDN timeout means Kemono unavailable
- **Probe ≠ download:** find/test-hash hard-kill aria2c and delete temp `mrf-test`. If user sees unexpected download after a probe, kill leftover `aria2c` (cmdline contains `mrf-test`) and clear that temp folder.
- **Junk magnets:** after rejecting a scam/dead torrent, delete its `torrents/<hash>.torrent` cache so it is not reused

### Anti-scam / anti-malware (mandatory)

`mrf inspect` reads **only** `aria2c -S` metadata (file names, sizes, extensions). It does **not** execute payload files.

| Signal | Examples | Action |
|--------|----------|--------|
| Dangerous ext | `.exe` `.chm` `.scr` `.bat` `.js` `.lnk` `.apk` | score↑ → often `scam` |
| Spam names | 约炮 / 外围 / 含羞草 / 福利平台 / fake APP ads | score↑ |
| BitComet padding | many `_____padding_file_*`, tiny real files | score↑ |
| No media | no `.mp4`/`.mkv`/… when user asked for video | score↑ |
| Fake size | advertised GB but real non-pad ≪ 5 MB | score↑ |

**Agent must:**

1. Run find (auto-inspects) or `uv run mrf inspect path/to.torrent --json` before download
2. **Never** call `mrf download` on `Verdict=scam` / `Status=scam`
3. Tell user clearly: seeders alive ≠ safe content
4. Reassure: metadata inspect + refused download = **no infection** from that magnet
5. If user pastes a magnet that inspect marks scam: explain reasons, delete cache, ask for a different hash/title

---

## Extend for new titles

Edit `src/mrf/queries.py` — add alias mapping in `ALIASES`.

Add example JSON under `examples/` for frequently requested media.

---

## Environment

```bash
uv sync                          # install deps into .venv
uv run pytest                    # unit tests
uv run mrf --help
```

System deps: **aria2c**, **ffprobe**/**ffmpeg** (see README prerequisites).

---

## More detail

- Troubleshooting: [`reference.md`](reference.md)
- Case studies: [`examples.md`](examples.md)
- Human quickstart: [`../README.md`](../README.md)
