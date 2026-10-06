"""Shared networking + pagination loop. Source-specific code lives in subclasses."""
import logging
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

import config

try:  # lxml is faster; fall back to the built-in parser if it is missing
    import lxml  # noqa: F401
    PARSER = "lxml"
except ImportError:  # pragma: no cover
    PARSER = "html.parser"


def create_session() -> requests.Session:
    """One session with User-Agent and retries (1s, 2s, 4s) for temporary errors."""
    session = requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT})
    retries = Retry(total=3, backoff_factor=1.0,
                    status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class BaseScraper:
    source_name = ""
    start_url = ""

    def __init__(self, session: Optional[requests.Session] = None,
                 delay: float = config.REQUEST_DELAY,
                 timeout: float = config.REQUEST_TIMEOUT,
                 max_pages: Optional[int] = None):
        self.session = session or create_session()
        self.delay = delay
        self.timeout = timeout
        self.max_pages = max_pages
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        """Download and parse one page. Returns None (and logs) on failure."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = "utf-8"  # keeps the pound sign correct
            return BeautifulSoup(response.text, PARSER)
        except requests.RequestException as exc:
            self.logger.error("Failed to fetch %s: %s", url, exc)
            return None
        finally:
            time.sleep(self.delay)

    def parse_page(self, soup: BeautifulSoup, page_url: str) -> list:
        raise NotImplementedError

    def scrape(self) -> list:
        """Follow the 'next' link until there is none (no hard-coded page count)."""
        url, page, records = self.start_url, 1, []
        while url:
            if self.max_pages and page > self.max_pages:
                self.logger.info("Reached max_pages=%d, stopping", self.max_pages)
                break
            self.logger.info("[%s] Page %d: %s", self.source_name, page, url)
            soup = self.fetch(url)
            if soup is None:
                self.logger.error("[%s] Stopping at page %d after failed request",
                                  self.source_name, page)
                break
            try:
                found = self.parse_page(soup, url)
            except Exception:  # a broken page must not kill the run
                self.logger.exception("Could not parse page %s", url)
                found = []
            records.extend(found)
            self.logger.info("[%s] Page %d: %d records", self.source_name, page, len(found))
            next_link = soup.select_one("li.next > a")
            href = next_link.get("href") if next_link else None
            url = urljoin(url, href) if href else None
            page += 1
        return records
