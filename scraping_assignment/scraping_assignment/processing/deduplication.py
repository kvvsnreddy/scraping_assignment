"""Fingerprint-based duplicate detection (duplicates are removed, not flagged)."""
import hashlib
import re

BOOKS = "Books to Scrape"


def make_fingerprint(rec: dict) -> str:
    """Books: source+title. Quotes: source+author+first 50 chars of quote."""
    title = rec.get("name_or_title") or ""
    if rec.get("source") == BOOKS:
        key = f'{rec.get("source")} {title}'
    else:
        key = f'{rec.get("source")} {rec.get("author") or ""} {title[:50]}'
    key = re.sub(r"[^\w\s]", "", key.lower())  # lowercase, drop punctuation
    key = " ".join(key.split())                # collapse spaces
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def find_duplicates(records):
    """Return (unique, duplicates); the first occurrence is kept."""
    seen, unique, dupes = set(), [], []
    for rec in records:
        fp = make_fingerprint(rec)
        (dupes if fp in seen else unique).append(rec)
        seen.add(fp)
    return unique, dupes
