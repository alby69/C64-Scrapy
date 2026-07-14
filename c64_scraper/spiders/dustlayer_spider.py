import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import time
from c64_scraper.items import DocItem
from c64_scraper.utils.processor import ContentProcessor

class DustlayerSpider(CrawlSpider):
    name = "dustlayer"
    allowed_domains = ["dustlayer.com"]
    start_urls = ["https://dustlayer.com/about"]

    # Crawl everything on dustlayer.com except binary assets or admin pages
    rules = (
        Rule(
            LinkExtractor(
                allow=(r"/c64-coding-tutorials/", r"/about", r"/articles/"),
                deny=(r"\.(zip|pdf|png|jpg|gif)$")
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
        item["category"] = "dustlayer"
        item["tags"] = ["c64", "tutorial", "assembly", "VIC-II"]
        item["body_md"] = body_md
        item["code_blocks"] = []

        # Dustlayer uses pre elements or code blocks for assembly
        for pre in response.css("pre"):
            code_text = "".join(pre.css("::text").getall()).strip()
            if code_text:
                lang = ContentProcessor.detect_language(code_text) or "asm"
                item["code_blocks"].append({"lang": lang, "code": code_text})

        item["scraped_at"] = time.strftime("%Y-%m-%d")
        if last_modified:
            item["last_modified"] = last_modified

        yield item
