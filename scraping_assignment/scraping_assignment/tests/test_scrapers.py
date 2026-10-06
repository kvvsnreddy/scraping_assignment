"""Offline scraper tests using fake HTML (no internet)."""
from bs4 import BeautifulSoup

from main import clean_and_validate
from scrapers.base_scraper import PARSER
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

BOOK_HTML = """<html><body>
<article class="product_pod"><h3><a href="{href}" title="Full Title Here">Full Title ...</a></h3>
<p class="star-rating Three"></p><div><p class="price_color">\u00a351.77</p></div></article>
<article class="product_pod"><h3></h3></article>
<ul class="pager">{nxt}</ul></body></html>"""

QUOTE_HTML = """<html><body>
<div class="quote"><span class="text">\u201cHi  there\u201d</span>
<span>by <small class="author">Ann\xa0Lee</small></span>
<div class="tags"><a class="tag">Zed</a><a class="tag">alpha</a></div></div>
<div class="quote"><small class="author">NoText</small></div>
<ul class="pager">{nxt}</ul></body></html>"""


def soup(html):
    return BeautifulSoup(html, PARSER)


class FakeSite:
    """Replaces fetch(): serves pages from a dict, returns None for unknown URLs."""
    def __init__(self, pages):
        self.pages = pages

    def fetch(self, url):
        html = self.pages.get(url)
        return soup(html) if html else None


class FakeBooks(FakeSite, BooksScraper):
    pass


class FakeQuotes(FakeSite, QuotesScraper):
    pass


def test_book_parsing_and_missing_elements():
    html = BOOK_HTML.format(href="a_1/index.html", nxt="")
    s = BooksScraper(delay=0, fetch_details=False)
    recs = s.parse_page(soup(html), "https://books.toscrape.com/catalogue/page-2.html")
    assert len(recs) == 2  # the broken article does not crash the page
    assert recs[0]["title"] == "Full Title Here"
    assert recs[0]["href"] == "https://books.toscrape.com/catalogue/a_1/index.html"
    assert recs[0]["rating_raw"] == "star-rating Three"
    assert recs[1]["title"] is None and recs[1]["price_raw"] is None


def test_quote_parsing():
    html = QUOTE_HTML.format(nxt="")
    recs = QuotesScraper(delay=0).parse_page(soup(html), "https://quotes.toscrape.com/")
    assert len(recs) == 2 and recs[0]["tags_raw"] == ["Zed", "alpha"]
    valid, stats = clean_and_validate("Quotes to Scrape", recs)
    assert len(valid) == 1  # second quote has no text -> rejected, not crashed
    assert stats["rejected_by_reason"] == {"missing_name": 1}
    assert valid[0]["author"] == "Ann Lee" and valid[0]["tags"] == "alpha;zed"
    assert valid[0]["name_or_title"] == "Hi there"


def test_pagination_follows_next_link_until_none():
    base = "https://quotes.toscrape.com/"
    pages = {
        base: QUOTE_HTML.format(nxt='<li class="next"><a href="/page/2/">next</a></li>'),
        base + "page/2/": QUOTE_HTML.format(nxt='<li class="next"><a href="/page/3/">next</a></li>'),
        base + "page/3/": QUOTE_HTML.format(nxt=""),
    }
    scraper = FakeQuotes.__new__(FakeQuotes)
    QuotesScraper.__init__(scraper, delay=0)
    FakeSite.__init__(scraper, pages)
    recs = scraper.scrape()
    assert len(recs) == 6  # 3 pages x 2 quotes, page count never hard-coded


def test_failed_page_stops_source_without_crashing():
    base = "https://quotes.toscrape.com/"
    pages = {base: QUOTE_HTML.format(nxt='<li class="next"><a href="/page/2/">n</a></li>')}
    scraper = FakeQuotes.__new__(FakeQuotes)
    QuotesScraper.__init__(scraper, delay=0)
    FakeSite.__init__(scraper, pages)  # page 2 missing -> fetch returns None
    assert len(scraper.scrape()) == 2


def test_max_pages_limit():
    base = "https://quotes.toscrape.com/"
    pages = {base: QUOTE_HTML.format(nxt='<li class="next"><a href="/page/2/">n</a></li>'),
             base + "page/2/": QUOTE_HTML.format(nxt="")}
    scraper = FakeQuotes.__new__(FakeQuotes)
    QuotesScraper.__init__(scraper, delay=0, max_pages=1)
    FakeSite.__init__(scraper, pages)
    assert len(scraper.scrape()) == 2
