"""Maps each source's raw dictionary onto the common data model (uses cleaning.py)."""
from processing import cleaning as c
import config


def clean_book(raw: dict) -> dict:
    return {
        "source": raw["source"],
        "source_url": c.normalize_url(raw.get("href")),
        "name_or_title": c.clean_text(raw.get("title")),
        "category": c.clean_text(raw.get("category_raw")),
        "price": c.clean_price(raw.get("price_raw")),
        "rating": c.clean_rating(raw.get("rating_raw")),
        "author": None,
        "tags": None,
        "description": c.clean_text(raw.get("description_raw")),
        "scraped_at": raw.get("scraped_at"),
    }


def clean_quote(raw: dict) -> dict:
    return {
        "source": raw["source"],
        "source_url": c.normalize_url(raw.get("page_url")),
        "name_or_title": c.strip_quotes(raw.get("text_raw")),
        "category": None,
        "price": None,
        "rating": None,
        "author": c.clean_text(raw.get("author_raw")),
        "tags": c.clean_tags(raw.get("tags_raw")),
        "description": None,
        "scraped_at": raw.get("scraped_at"),
    }


CLEANERS = {config.BOOKS_SOURCE: clean_book, config.QUOTES_SOURCE: clean_quote}
