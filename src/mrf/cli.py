"""Typer CLI: `uv run mrf <command>`."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from mrf import __version__
from mrf.compress import compress_dir
from mrf.download import download
from mrf.fetch import fetch_torrent
from mrf.find import find, pick_best
from mrf.hashutil import normalize_hash
from mrf.inspect_torrent import inspect_torrent
from mrf.kemono import download_attachment, fetch_post
from mrf.paths import last_find_path, project_root
from mrf.probe import probe_seeders
from mrf.queries import build_queries
from mrf.thumbnails import fix_thumbnails
from mrf.verify import verify_dir

app = typer.Typer(
    name="mrf",
    help="Media Resource Finder — find / inspect / download / verify (cross-platform).",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.callback()
def _root(
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
) -> None:
    if version:
        console.print(f"mrf {__version__}")
        raise typer.Exit(0)


@app.command("find")
def cmd_find(
    query: str = typer.Argument(..., help="Search text (movie title, creator, filename)"),
    hash: Optional[list[str]] = typer.Option(
        None, "--hash", "-H", help="Known 40-char info-hash (repeatable)"
    ),
    skip_test: bool = typer.Option(False, "--skip-test", help="Skip seeder probe"),
    test_seconds: int = typer.Option(45, "--test-seconds", help="Probe timeout per hash"),
) -> None:
    """Search BTDig, inspect torrents, probe seeders."""
    console.print("[cyan]=== Media Resource Finder ===[/cyan]")
    console.print(f"Request: {query}\n")
    queries = build_queries(query)
    console.print("Search queries:")
    for q in queries:
        console.print(f"  - {q}")
    console.print()

    try:
        results = find(
            query,
            hashes=hash or [],
            skip_test=skip_test,
            test_seconds=test_seconds,
        )
    except LookupError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        raise typer.Exit(1) from exc

    table = Table(title="Results")
    table.add_column("Hash")
    table.add_column("SD")
    table.add_column("Status")
    table.add_column("Name")
    for r in results:
        table.add_row(r.hash, str(r.seeders), r.status, r.name[:60])
    console.print(table)

    scam_n = sum(1 for r in results if r.status == "scam")
    if scam_n:
        console.print(
            f"[red]Blocked {scam_n} scam/junk torrent(s). Cache deleted. Do NOT download those hashes.[/red]"
        )

    best = pick_best(results)
    root = project_root()
    if best and best.status == "alive":
        console.print("[green]Recommended download:[/green]")
        console.print(f"  cd {root}")
        console.print(f"  uv run mrf download {best.hash}")
    elif best and best.status == "suspicious":
        console.print("[yellow]Only SUSPICIOUS candidate (has seeders but failed scam checks):[/yellow]")
        console.print(f"  Hash: {best.hash}  Seeders: {best.seeders}")
        console.print("  Warn user; only download with --force if they insist after review.")
        console.print(f"  uv run mrf download {best.hash} --force")
    else:
        console.print("[yellow]No clean hash with seeders found.[/yellow]")
        console.print('Try: WebSearch for more hashes, or `mrf find "..." --hash <hash>`')

    console.print(f"Report: {last_find_path(root)}")
    if not any(r.status == "alive" for r in results):
        raise typer.Exit(1)


@app.command("download")
def cmd_download(
    hash_value: str = typer.Argument(..., help="40-char info-hash or magnet"),
    select_file: Optional[list[int]] = typer.Option(
        None, "--select-file", "-s", help="aria2 file index (repeatable)"
    ),
    videos_only: bool = typer.Option(False, "--videos-only", help="Download mp4 only"),
    force: bool = typer.Option(False, "--force", help="Allow suspicious/scam after review"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o"),
    seed_ratio: float = typer.Option(0.0, "--seed-ratio"),
    seed_time: int = typer.Option(0, "--seed-time"),
) -> None:
    """Download torrent (inspect gate first)."""
    try:
        h = normalize_hash(hash_value)
        console.print(f"Hash   : {h}")
        out = download(
            h,
            output_dir=output_dir,
            select_file=select_file or [],
            videos_only=videos_only,
            force=force,
            seed_ratio=seed_ratio,
            seed_time=seed_time,
        )
        console.print(f"[green]Done → {out}[/green]")
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        msg = str(exc).lower()
        code = 2 if "scam" in msg else 1
        raise typer.Exit(code) from exc


@app.command("inspect")
def cmd_inspect(
    torrent: Path = typer.Argument(..., help="Path to .torrent"),
    json_out: bool = typer.Option(False, "--json", help="Print JSON report"),
) -> None:
    """Inspect torrent metadata for scam/malware signals."""
    try:
        report = inspect_torrent(torrent)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(3) from exc

    if json_out:
        console.print_json(data=report.to_json_dict())
    else:
        color = {"clean": "green", "suspicious": "yellow", "scam": "red"}[report.verdict]
        console.print(
            f"[{color}]Inspect: {report.verdict} (score={report.score})  {report.name}[/{color}]"
        )
        for r in report.reasons:
            console.print(f"  - {r}")
        if report.media_count:
            mb = round(report.media_bytes / (1024 * 1024), 1)
            console.print(f"  media: {report.media_count} file(s), {mb} MB")
        console.print(
            f"VERDICT={report.verdict} SCORE={report.score} "
            f"MEDIA={report.media_count} DANGER={report.dangerous_count}"
        )
    raise typer.Exit(report.exit_code)


@app.command("verify")
def cmd_verify(
    directory: Path = typer.Argument(..., help="Folder with MP4s"),
    recursive: bool = typer.Option(False, "--recursive", "-r"),
) -> None:
    """Check MP4 files are complete and playable."""
    try:
        results = verify_dir(directory, recursive=recursive)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    console.print("[cyan]=== Video Verification ===[/cyan]")
    console.print(f"Folder: {directory}  |  Files: {len(results)}\n")
    ok = sum(1 for r in results if r.ok)
    console.print(f"Passed: {ok} / {len(results)}")
    bad = [r for r in results if not r.ok]
    for r in bad:
        console.print(f"[yellow]  FAIL: {r.path.name} - {r.detail}[/yellow]")
    if bad:
        raise typer.Exit(1)
    console.print("[green]All videos OK.[/green]")


@app.command("test-hash")
def cmd_test_hash(
    hash_value: str = typer.Argument(...),
    timeout: int = typer.Option(60, "--timeout"),
) -> None:
    """Fetch torrent and probe seeders for one hash."""
    try:
        h = normalize_hash(hash_value)
        tp = fetch_torrent(h)
        sd = probe_seeders(tp, timeout_sec=timeout)
        console.print(f"Hash: {h}  Seeders: {sd}")
        raise typer.Exit(0 if sd >= 1 else 1)
    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc


@app.command("fetch-torrent")
def cmd_fetch(
    hash_value: str = typer.Argument(...),
    out_dir: Optional[Path] = typer.Option(None, "--out-dir"),
    magnet_timeout: int = typer.Option(120, "--magnet-timeout"),
) -> None:
    """Download .torrent from cache or magnet metadata."""
    try:
        path = fetch_torrent(hash_value, out_dir=out_dir, magnet_timeout=magnet_timeout)
        console.print(f"Fetched: {path}")
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command("kemono")
def cmd_kemono(
    user: str = typer.Option(..., "--user"),
    post: str = typer.Option(..., "--post"),
    service: str = typer.Option("patreon", "--service"),
    file: Optional[str] = typer.Option(None, "--file", help="Attachment name to download"),
    out_dir: Optional[Path] = typer.Option(None, "--out-dir"),
) -> None:
    """List or download Kemono/Pawchive post attachments."""
    try:
        data = fetch_post(service, user, post)
        console.print(f"Title: {data.get('title')}")
        console.print(f"has_full: {data.get('has_full')}")
        console.print("Attachments:")
        for i, a in enumerate(data.get("attachments") or [], 1):
            console.print(f"  [{i}] {a.get('name')}")
        if not file:
            console.print(
                f'\nDownload: uv run mrf kemono --user {user} --post {post} --file "name.mp4"'
            )
            return
        path = download_attachment(service, user, post, file, out_dir=out_dir)
        console.print(f"[green]Success: {path}[/green]")
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command("compress")
def cmd_compress(
    directory: Path = typer.Argument(...),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir"),
    recursive: bool = typer.Option(False, "--recursive", "-r"),
    encoder: str = typer.Option("qsv", "--encoder", help="qsv|nvenc|av1|x265"),
    cq: int = typer.Option(0, "--cq"),
    nv_preset: str = typer.Option("p1", "--nv-preset"),
    x265_preset: str = typer.Option("fast", "--x265-preset"),
    replace: bool = typer.Option(False, "--replace"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    skip_existing: bool = typer.Option(False, "--skip-existing"),
) -> None:
    """Re-encode MP4s to smaller HEVC/AV1."""
    if encoder not in {"qsv", "nvenc", "av1", "x265"}:
        console.print("[red]encoder must be qsv|nvenc|av1|x265[/red]")
        raise typer.Exit(1)
    try:
        summary = compress_dir(
            directory,
            output_dir=output_dir,
            recursive=recursive,
            encoder=encoder,  # type: ignore[arg-type]
            cq=cq,
            nv_preset=nv_preset,
            x265_preset=x265_preset,
            replace=replace,
            dry_run=dry_run,
            skip_existing=skip_existing,
        )
        console.print(f"Done: {summary.done}  Failed: {len(summary.failed)}")
        if summary.output_dir:
            console.print(f"Output: {summary.output_dir}")
        if summary.failed:
            raise typer.Exit(1)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command("fix-thumbnails")
def cmd_thumbs(
    directory: Path = typer.Argument(...),
    recursive: bool = typer.Option(False, "--recursive", "-r"),
    embed_cover: bool = typer.Option(False, "--embed-cover"),
    cache_only: bool = typer.Option(False, "--cache-only"),
) -> None:
    """Fix Windows Explorer video thumbnails (Windows only for cache clear)."""
    if sys.platform != "win32" and not embed_cover:
        console.print(
            "[yellow]Thumbnail cache clear is Windows-only. Use --embed-cover for poster embed.[/yellow]"
        )
    try:
        stats = fix_thumbnails(
            directory,
            recursive=recursive,
            embed_cover_flag=embed_cover,
            cache_only=cache_only,
        )
        console.print(
            f"Files: {stats['files']}  Embedded: {stats['embedded']}  "
            f"Cache removed: {stats['cache_removed']}"
        )
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command("queries")
def cmd_queries(query: str = typer.Argument(...)) -> None:
    """Print expanded search queries for a request."""
    for q in build_queries(query):
        console.print(q)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
