"""Books to Scrape: selectors, pagination and raw dictionaries."""
from datetime import datetime, timezone
from urllib.parse import urljoin

import config
from scrapers.base_scraper import BaseScraper


class BooksScraper(BaseScraper):
    source_name = config.BOOKS_SOURCE
    start_url = config.BOOKS_START_URL

    def __init__(self, *args, fetch_details: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetch_details = fetch_details  # visit each detail page for category/description

    def parse_page(self, soup, page_url):
        records = []
        for article in soup.select("article.product_pod"):
            try:
                records.append(self.parse_book(article, page_url))
            except Exception:
                self.logger.exception("Skipping one book on %s", page_url)
        return records

    def parse_book(self, article, page_url):
        link = article.select_one("h3 > a")
        price = article.select_one("p.price_color")
        rating = article.select_one("p.star-rating")
        href = urljoin(page_url, link["href"]) if link and link.get("href") else None
        raw = {
            "source": self.source_name,
            "title": (link.get("title") or link.get_text()) if link else None,
            "href": href,
            "price_raw": price.get_text() if price else None,
            "rating_raw": " ".join(rating.get("class", [])) if rating else None,
            "category_raw": None,
            "description_raw": None,
            "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        if self.fetch_details and href:
            self.add_details(raw, href)
        return raw

    def add_details(self, raw, detail_url):
        soup = self.fetch(detail_url)
        if soup is None:
            self.logger.warning("No detail page for %s; category/description left empty", detail_url)
            return
        crumbs = soup.select("ul.breadcrumb li")
        if len(crumbs) >= 3:  # Home > Books > <Category> > Title
            raw["category_raw"] = crumbs[2].get_text()
        desc_header = soup.select_one("#product_description")
        if desc_header:
            para = desc_header.find_next_sibling("p")
            raw["description_raw"] = para.get_text() if para else None
