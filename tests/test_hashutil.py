import pytest

from mrf.hashutil import normalize_hash, try_normalize_hash


def test_plain_hash():
    h = "5E3420E20E2AE55FD13E9A2F5CAEF7D9CB8E7ECB"
    assert normalize_hash(h) == h.lower()


def test_magnet():
    mag = "magnet:?xt=urn:btih:5E3420E20E2AE55FD13E9A2F5CAEF7D9CB8E7ECB&dn=foo"
    assert (
        normalize_hash(mag) == "5e3420e20e2ae55fd13e9a2f5caef7d9cb8e7ecb"
    )


def test_invalid():
    with pytest.raises(ValueError):
        normalize_hash("abc")
    assert try_normalize_hash("abc") is None
