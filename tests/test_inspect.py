from pathlib import Path

from mrf.inspect_torrent import inspect_listing

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_scam_mixed_chm_and_mp4():
    report = inspect_listing(_load("scam_mixed.listing"))
    assert report.verdict == "scam"
    assert report.score >= 50
    assert report.dangerous_count >= 1
    assert report.media_count >= 1
    assert any("dangerous_ext" in r for r in report.reasons)
    assert report.exit_code == 2


def test_clean_video():
    report = inspect_listing(_load("clean_video.listing"))
    assert report.verdict == "clean"
    assert report.score < 25
    assert report.media_count == 1
    assert report.exit_code == 0


def test_spam_name_boost():
    listing = _load("clean_video.listing").replace(
        "Avatar.Fire.and.Ash.2025.1080p.mkv",
        "约炮福利平台.mp4",
    )
    # also fix Name line
    listing = listing.replace(
        "Name: Avatar.Fire.and.Ash.2025.1080p.mkv",
        "Name: 约炮福利平台",
    )
    report = inspect_listing(listing)
    assert report.score >= 25
    assert any("spam_name" in r for r in report.reasons)
