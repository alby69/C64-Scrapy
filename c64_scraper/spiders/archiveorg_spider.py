import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import time
from c64_scraper.items import DocItem
from c64_scraper.utils.processor import ContentProcessor

class ArchiveOrgSpider(CrawlSpider):
    name = "archiveorg"
    allowed_domains = ["archive.org"]
    start_urls = ["https://archive.org/details/commodore-64-books"]

    # Simple rules to stay within collections or specific item pages
    rules = (
        Rule(
            LinkExtractor(
                allow=(r"/details/"),
                deny=(r"/download/")
            ),
            callback="parse_item",
            follow=True
        ),
    )

    def parse_item(self, response):
        if "text/html" not in response.headers.get("Content-Type", b"").decode(errors="ignore"):
            return

        html = response.text
        title = (response.css("h1.item-title::text").get() or response.css("title::text").get() or response.url).strip()

        # Extract markdown content (mostly metadata or text representation on detail pages)
        body_md = ContentProcessor.extract_markdown(html, response.url)

        # Get last modified header if present
        last_mod_header = response.headers.get("Last-Modified")
        last_modified = last_mod_header.decode("utf-8", errors="ignore") if last_mod_header else None

        item = DocItem()
        item["url"] = response.url
        item["title"] = title
        item["category"] = "archiveorg"
        item["tags"] = ["c64", "archive", "books", "manuals"]
        item["body_md"] = body_md
        item["code_blocks"] = []
        item["scraped_at"] = time.strftime("%Y-%m-%d")
        if last_modified:
            item["last_modified"] = last_modified

        yield item
