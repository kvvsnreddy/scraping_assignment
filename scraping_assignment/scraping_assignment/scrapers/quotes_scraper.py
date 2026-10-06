"""Quotes to Scrape: selectors, pagination and raw dictionaries."""
from datetime import datetime, timezone

import config
from scrapers.base_scraper import BaseScraper


class QuotesScraper(BaseScraper):
    source_name = config.QUOTES_SOURCE
    start_url = config.QUOTES_START_URL

    def parse_page(self, soup, page_url):
        records = []
        for block in soup.select("div.quote"):
            try:
                records.append(self.parse_quote(block, page_url))
            except Exception:
                self.logger.exception("Skipping one quote on %s", page_url)
        return records

    def parse_quote(self, block, page_url):
        text = block.select_one("span.text")
        author = block.select_one("small.author")
        return {
            "source": self.source_name,
            "text_raw": text.get_text() if text else None,
            "author_raw": author.get_text() if author else None,
            "tags_raw": [t.get_text() for t in block.select("a.tag")],
            "page_url": page_url,  # source_url = page where the quote appeared
            "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
