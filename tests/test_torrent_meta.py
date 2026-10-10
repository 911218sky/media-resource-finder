from pathlib import Path

from mrf.torrent_meta import parse_listing

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_mixed():
    meta = parse_listing((FIXTURES / "scam_mixed.listing").read_text(encoding="utf-8"))
    assert meta.hash == "5e3420e20e2ae55fd13e9a2f5caef7d9cb8e7ecb"
    assert len(meta.files) == 2
    assert meta.files[0].ext == ".chm"
    assert meta.files[1].ext == ".mp4"
    assert meta.total_bytes == 1_073_741_824
