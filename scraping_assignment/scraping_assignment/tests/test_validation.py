from processing.validation import validate_record


def good():
    return {"source": "Books to Scrape", "name_or_title": "T", "source_url": "https://x.com",
            "price": 10.0, "rating": 3}


def test_valid_record():
    assert validate_record(good()) == []


def test_missing_optional_fields_ok():
    rec = good()
    rec["price"] = rec["rating"] = None
    assert validate_record(rec) == []


def test_each_problem_reported():
    rec = {"source": "Other", "name_or_title": "", "source_url": "ftp://x",
           "price": -1, "rating": 9}
    assert set(validate_record(rec)) == {"unknown_source", "missing_name", "invalid_url",
                                         "invalid_price", "invalid_rating"}


def test_non_numeric_price():
    rec = good()
    rec["price"] = "12"
    assert validate_record(rec) == ["invalid_price"]
