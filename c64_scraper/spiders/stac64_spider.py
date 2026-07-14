import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import time
from c64_scraper.items import DocItem
from c64_scraper.utils.processor import ContentProcessor

class StaC64Spider(CrawlSpider):
    name = "stac64"
    allowed_domains = ["sta.c64.org"]
    start_urls = ["https://sta.c64.org/cbmdocs.html"]

    rules = (
        Rule(
            LinkExtractor(
                allow=(r"cbm.*\.html$", r"cbmdocs\.html$"),
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
        title = (response.css("h1::text").get() or response.css("title::text").get() or response.url).strip()

        # Extract markdown content
        body_md = ContentProcessor.extract_markdown(html, response.url)

        # Get last modified header if present
        last_mod_header = response.headers.get("Last-Modified")
        last_modified = last_mod_header.decode("utf-8", errors="ignore") if last_mod_header else None

        item = DocItem()
        item["url"] = response.url
        item["title"] = title
        item["category"] = "sta_c64"
        item["tags"] = ["c64", "reference", "hardware", "memory_map"]
        item["body_md"] = body_md
        item["code_blocks"] = []

        # Extract pre formatted text or tables if they contain code/memory maps
        for pre in response.css("pre"):
            code_text = "".join(pre.css("::text").getall()).strip()
            if code_text:
                lang = ContentProcessor.detect_language(code_text) or "asm"
                item["code_blocks"].append({"lang": lang, "code": code_text})

        item["scraped_at"] = time.strftime("%Y-%m-%d")
        if last_modified:
            item["last_modified"] = last_modified

        yield item
