from processing.cleaning import (clean_price, clean_rating, clean_tags, clean_text,
                                 normalize_url, strip_quotes)


def test_clean_text():
    assert clean_text(" Hello \n World ") == "Hello World"
    assert clean_text("a\xa0\xa0b\tc") == "a b c"
    assert clean_text("   ") is None
    assert clean_text(None) is None


def test_strip_quotes():
    assert strip_quotes("\u201cThe world.\u201d") == "The world."
    assert strip_quotes("  \u201c x \u201d ") == "x"


def test_clean_price():
    assert clean_price("\u00a351.77") == 51.77
    assert clean_price("\u00c2\u00a351.77") == 51.77  # mis-decoded pound sign
    assert clean_price("\u00a31,234.50") == 1234.5
    assert clean_price("free") is None
    assert clean_price(None) is None


def test_clean_rating():
    assert clean_rating("star-rating Three") == 3
    assert clean_rating("Five") == 5
    assert clean_rating("star-rating") is None
    assert clean_rating(None) is None


def test_clean_tags():
    assert clean_tags(["Love", " life ", "love"]) == "life;love"
    assert clean_tags([]) is None
    assert clean_tags(None) is None


def test_normalize_url():
    assert normalize_url("catalogue/x/index.html", base="https://books.toscrape.com/") == \
        "https://books.toscrape.com/catalogue/x/index.html"
    assert normalize_url("ftp://x") is None
    assert normalize_url("/relative") is None
    assert normalize_url(None) is None
