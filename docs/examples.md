# Examples

## Example 1: Iron Man 3 (鋼鐵人3)

**Goal:** Find and download a mainstream movie release.

```bash
cd <project-root>

uv run mrf find "Iron Man 3"
# or
uv run mrf find "鋼鐵人3"

# After find reports a clean hash with SD >= 1:
uv run mrf download <40-char-hash>
uv run mrf verify ./downloads --recursive
```

Prefer Disney+ / digital purchase when available.

See also: `examples/iron-man-3.json`

---

## Example 2: Avatar 3 (Fire and Ash 2025)

```bash
uv run mrf find "Avatar 3"
uv run mrf download <40-char-hash>
uv run mrf verify ./downloads --recursive
```

See also: `examples/avatar-fire-and-ash.json`

---

## Example 3: Select one file from a multi-file torrent

```bash
aria2c -S "./torrents/HASH.torrent" | grep -i "Iron.Man.3"
# Output: N|./path/Iron.Man.3.1080p.mp4  → use -s N
uv run mrf download HASH -s N
```

---

## Example 4: Compress after download

```bash
uv run mrf compress ./downloads --recursive --encoder qsv
uv run mrf verify ./downloads-compressed --recursive
```
