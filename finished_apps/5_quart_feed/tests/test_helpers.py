from utils.helpers import likes_line, linkify


def test_likes_line_empty():
    assert str(likes_line([])) == ""


def test_likes_line_one():
    s = str(likes_line(["alice"]))
    assert '<a href="/user/alice">alice</a> liked this' in s


def test_likes_line_few():
    s = str(likes_line(["a", "b", "c"]))
    assert " and " in s and "liked this" in s
    for u in ("a", "b", "c"):
        assert '/user/%s' % u in s  # each name is a profile link


def test_likes_line_collapses_over_five():
    s = str(likes_line(["u1", "u2", "u3", "u4", "u5", "u6", "u7"]))  # 7 > 5
    assert "4 other people" in s  # 7 - 3 shown
    assert "likers-more" in s and "likers-full" in s
    assert "/user/u1" in s and "/user/u7" in s  # first shown + present in full list


def test_linkify_escapes_and_links():
    s = str(linkify("hi <b> http://example.com/x"))
    assert "&lt;b&gt;" in s  # non-URL text escaped
    assert '<a href="http://example.com/x"' in s


def test_linkify_truncates_long_url():
    url = "http://example.com/" + "a" * 100
    s = str(linkify(url))
    assert "…" in s  # display truncated
    assert 'href="' + url + '"' in s  # href keeps the full URL
