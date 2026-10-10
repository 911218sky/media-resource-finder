from mrf.queries import build_queries


def test_avatar_alias():
    qs = build_queries("Avatar 3")
    assert "Avatar 3" in qs
    assert any("Fire and Ash" in q for q in qs)


def test_iron_man_3():
    qs = build_queries("Iron Man 3")
    assert "Iron Man 3" in qs
    assert any("2013" in q for q in qs)
    assert any("1080p" in q for q in qs)


def test_iron_man_3_chinese_alias():
    qs = build_queries("鋼鐵人3")
    assert any("Iron Man 3" in q for q in qs)
