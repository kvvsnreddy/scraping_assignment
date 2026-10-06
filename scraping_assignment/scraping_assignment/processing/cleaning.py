"""Small pure functions: value in, cleaned value out. No internet, no files."""
import re
from typing import Iterable, Optional
from urllib.parse import urljoin

RATING_MAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
_QUOTE_CHARS = "\u201c\u201d\u2018\u2019\"'"


def clean_text(value: Optional[str]) -> Optional[str]:
    """Collapse all whitespace (incl. non-breaking spaces); empty -> None."""
    if value is None:
        return None
    text = " ".join(str(value).replace("\xa0", " ").split())
    return text or None


def strip_quotes(value: Optional[str]) -> Optional[str]:
    """Remove the quotation marks wrapped around quote text."""
    text = clean_text(value)
    if text is None:
        return None
    return clean_text(text.strip(_QUOTE_CHARS))


def clean_price(raw: Optional[str]) -> Optional[float]:
    """'£51.77' -> 51.77 (also handles 'Â£51.77' and '1,234.50')."""
    if not raw:
        return None
    match = re.search(r"\d+(?:\.\d+)?", str(raw).replace(",", ""))
    return float(match.group()) if match else None


def clean_rating(raw: Optional[str]) -> Optional[int]:
    """'star-rating Three' -> 3."""
    for word in (raw or "").lower().split():
        if word in RATING_MAP:
            return RATING_MAP[word]
    return None


def clean_tags(tags: Optional[Iterable[str]]) -> Optional[str]:
    """['Love', 'life'] -> 'life;love' (lowercase, de-duplicated, sorted)."""
    if not tags:
        return None
    cleaned = {t.lower() for t in (clean_text(x) for x in tags) if t}
    return ";".join(sorted(cleaned)) or None


def normalize_url(url: Optional[str], base: Optional[str] = None) -> Optional[str]:
    """Return a complete http(s) URL, or None if that is impossible."""
    url = clean_text(url)
    if not url:
        return None
    if base:
        url = urljoin(base, url)
    return url if url.lower().startswith(("http://", "https://")) else None
