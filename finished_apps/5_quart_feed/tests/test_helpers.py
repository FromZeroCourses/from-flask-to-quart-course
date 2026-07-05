from utils.helpers import likes_line, linkify


def test_likes_line_empty():
    assert str(likes_line([])) == ""


def test_likes_line_one():
    assert "alice liked this" in str(likes_line(["alice"]))


def test_likes_line_few():
    assert "a, b and c liked this" in str(likes_line(["a", "b", "c"]))


def test_likes_line_collapses_over_five():
    s = str(likes_line(["u1", "u2", "u3", "u4", "u5", "u6", "u7"]))  # 7 > 5
    assert "u1, u2, u3 and " in s
    assert "4 other people" in s  # 7 - 3 shown
    assert "likers-more" in s and "likers-full" in s


def test_linkify_escapes_and_links():
    s = str(linkify("hi <b> http://example.com/x"))
    assert "&lt;b&gt;" in s  # non-URL text escaped
    assert '<a href="http://example.com/x"' in s


def test_linkify_truncates_long_url():
    url = "http://example.com/" + "a" * 100
    s = str(linkify(url))
    assert "…" in s  # display truncated
    assert 'href="' + url + '"' in s  # href keeps the full URL
