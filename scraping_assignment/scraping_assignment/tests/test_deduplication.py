from processing.deduplication import find_duplicates, make_fingerprint


def test_duplicates_ignore_case_and_spaces():
    base = {"source": "Books to Scrape", "author": None}
    records = [{**base, "name_or_title": "Example Book Title"},
               {**base, "name_or_title": " Example Book Title "},
               {**base, "name_or_title": "EXAMPLE BOOK TITLE"}]
    unique, dupes = find_duplicates(records)
    assert len(unique) == 1 and len(dupes) == 2


def test_punctuation_ignored():
    a = {"source": "Books to Scrape", "name_or_title": "It's a Book!"}
    b = {"source": "Books to Scrape", "name_or_title": "its a book"}
    assert make_fingerprint(a) == make_fingerprint(b)


def test_quotes_use_author_and_first_50_chars():
    q = {"source": "Quotes to Scrape", "author": "A", "name_or_title": "x" * 60}
    same_prefix = {**q, "name_or_title": "x" * 50 + "different ending"}
    other_author = {**q, "author": "B"}
    unique, dupes = find_duplicates([q, same_prefix, other_author])
    assert len(unique) == 2 and len(dupes) == 1


def test_same_title_different_source_is_not_duplicate():
    a = {"source": "Books to Scrape", "name_or_title": "Same"}
    b = {"source": "Quotes to Scrape", "author": "", "name_or_title": "Same"}
    assert len(find_duplicates([a, b])[0]) == 2
