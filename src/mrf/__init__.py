"""Media Resource Finder — cross-platform torrent find/download toolkit."""

__version__ = "0.1.0"


def main() -> None:
    from mrf.cli import main as cli_main

    cli_main()
