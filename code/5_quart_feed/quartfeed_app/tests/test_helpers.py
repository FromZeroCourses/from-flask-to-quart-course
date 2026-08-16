from utils.helpers import linkify


def test_linkify_escapes_and_links():
    s = str(linkify("hi <b> http://example.com/x"))
    assert "&lt;b&gt;" in s  # non-URL text escaped
    assert '<a href="http://example.com/x"' in s


def test_linkify_truncates_long_url():
    url = "http://example.com/" + "a" * 100
    s = str(linkify(url))
    assert "…" in s  # display truncated
    assert 'href="' + url + '"' in s  # href keeps the full URL
