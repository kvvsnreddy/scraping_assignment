# Multi-Source Web Scraping & Data Consolidation

A small ETL pipeline: **scrape -> clean -> validate -> deduplicate -> consolidate -> save**.
Sources: [Books to Scrape](https://books.toscrape.com/) and [Quotes to Scrape](https://quotes.toscrape.com/).

## Python version & setup
Python 3.10 - 3.12 (developed on 3.12).
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
Dependencies: `requests`, `beautifulsoup4`, `lxml` (runtime); `pytest` (tests only).
> Before submitting, run `pip freeze` in your own venv and pin the exact versions you used.

## How to run
```bash
python main.py                 # full run (~1,000 book detail pages => roughly 10 min at 0.5s/request)
python main.py --no-details    # skip book detail pages (fast; category/description stay empty)
python main.py --max-pages 2   # quick smoke test
python -m pytest               # unit tests, no internet needed
```
Outputs: `output/final_dataset.csv`, `output/summary_report.json`, `logs/scraper.log`.

## Source exploration (what the HTML looks like)
| Item | Books to Scrape | Quotes to Scrape |
|---|---|---|
| Record | `article.product_pod` | `div.quote` |
| Main text | `h3 > a` (full title in `title` attribute; visible text is truncated with `...`) | `span.text` (wrapped in curly quotes) |
| Price | `p.price_color` (`£51.77`) | - |
| Rating | class on `p.star-rating` (`Three`) | - |
| Author / tags | - | `small.author` / `a.tag` |
| Link | `h3 > a[href]` (relative) | page URL (see below) |
| Next page | `li.next > a` | `li.next > a` |
| Category / description | only on the detail page (breadcrumb 3rd item; `#product_description` + `p`) | - |

Both sites are server-rendered HTML, so Requests + BeautifulSoup is enough; Selenium/Playwright would only add overhead.

## How pagination works
`BaseScraper.scrape()` starts at the home page, parses it, looks for `li.next > a`, joins its relative `href` onto the current URL with `urljoin`, and repeats until no next link exists. No page count is hard-coded. If a page fails after retries, that source stops (logged as ERROR) and the other source still runs.

## Data model
Columns (fixed order): `source, source_url, name_or_title, category, price, rating, author, tags, description, scraped_at`.
Non-applicable fields are left empty (never invented, e.g. quotes have no price).

| Column | Books | Quotes |
|---|---|---|
| source_url | book detail page URL | **page URL where the quote appeared** (chosen over author page) |
| name_or_title | book title | quote text without curly quotes |
| category / description | from detail page (empty if detail page fails or `--no-details`) | empty |
| price / rating | float / int 1-5 | empty |
| author / tags | empty | author / `tag1;tag2` (lowercase, sorted) |
| scraped_at | UTC ISO timestamp | UTC ISO timestamp |

Book availability is not part of the schema (not in the required columns).

## Cleaning (`processing/cleaning.py`, `transform.py`)
Pure functions: `clean_text` (collapses whitespace incl. `\xa0`, empty -> None), `strip_quotes`, `clean_price` (`£51.77` -> 51.77), `clean_rating` (`Three` -> 3), `clean_tags`, `normalize_url`. Responses are decoded as UTF-8 so `£` is not corrupted. `transform.py` maps each source's raw dict onto the common model.

## Validation (`processing/validation.py`)
Returns a list of problem codes per record: `unknown_source`, `missing_name`, `invalid_url`, `invalid_price` (non-numeric or < 0), `invalid_rating` (not 1-5). Invalid records are logged as WARNING, counted by reason in the summary, and excluded. A record with several problems increments each reason (so reason counts can exceed the rejected-record count).

## Deduplication (`processing/deduplication.py`)
Fingerprint = SHA-256 of the lowercased, punctuation-stripped, whitespace-collapsed key:
- Books: `source + title`
- Quotes: `source + author + first 50 characters of quote text`

First occurrence is kept; later matches are **removed** (not flagged) so the CSV has one row per real-world item and no extra column. Each removed duplicate is logged. The live sites contain unique items, so a real run is expected to find ~0 duplicates; the logic is proven by `tests/test_deduplication.py`.

## Error handling & logging
- Retries with exponential backoff (1s, 2s, 4s) for HTTP 429/500/502/503/504; 10s timeout; 0.5s pause between requests.
- Per-record `try/except` + `select_one()` None checks: a bad record is skipped, not fatal.
- Failed book detail page: warning, category/description left empty, the book is still kept.
- Each source runs in its own `try/except` in `main.py`.
- Logging goes to console and `logs/scraper.log` (INFO per page, WARNING per rejected/duplicate record, ERROR per failed request).

## Output & summary report
`summary_report.json` holds per-source and total counts: collected, cleaned, rejected (with reasons), duplicates, final, start/end time and duration, plus `reconciles` (`collected - rejected - duplicates == final`).

## Assumptions
- Practice-site layouts stay as described above.
- A quote is identified by author + first 50 characters; two different quotes sharing those would be treated as duplicates.

## Known limitations
- Full run is slow because of ~1,000 detail-page requests and the polite delay (sequential by design).
- No checkpoint/resume; a crash mid-run restarts from scratch.
- If a listing page fails, later pages of that source are skipped.
- Author "about" details from author pages are not collected.

## Production ideas
Checkpoint/resume, config file, scheduled runs with alerting, storing to a database, incremental scraping.

## AI usage summary
See `AI_USAGE.md`.
