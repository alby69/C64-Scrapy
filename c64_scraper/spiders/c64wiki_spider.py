import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import time
from c64_scraper.items import DocItem
from c64_scraper.utils.processor import ContentProcessor

class C64WikiSpider(CrawlSpider):
    name = "c64wiki"
    allowed_domains = ["c64-wiki.com", "www.c64-wiki.com"]
    start_urls = ["https://www.c64-wiki.com/wiki/Portal:Programming"]

    # Rules to follow wiki links, avoiding non-article namespaces
    rules = (
        Rule(
            LinkExtractor(
                allow=(r"/wiki/"),
                deny=(
                    r"/wiki/Special:",
                    r"/wiki/Category:",
                    r"/wiki/File:",
                    r"/wiki/Talk:",
                    r"/wiki/User:",
                    r"/wiki/Help:",
                    r"/wiki/Template:",
                    r"/wiki/C64-Wiki:",
                )
            ),
            callback="parse_item",
            follow=True
        ),
    )

    def parse_item(self, response):
        if "text/html" not in response.headers.get("Content-Type", b"").decode(errors="ignore"):
            return

        html = response.text
        title = (response.css("h1#firstHeading::text").get() or response.css("title::text").get() or response.url).strip()

        # Extract markdown content
        body_md = ContentProcessor.extract_markdown(html, response.url)

        # Get last modified header
        last_mod_header = response.headers.get("Last-Modified")
        last_modified = last_mod_header.decode("utf-8", errors="ignore") if last_mod_header else None

        item = DocItem()
        item["url"] = response.url
        item["title"] = title
        item["category"] = "c64wiki"
        item["tags"] = ["c64", "wiki", "reference"]
        item["body_md"] = body_md
        item["code_blocks"] = []  # Can extract pre/code or pre.mw-code if present

        # Try to extract code blocks from wikimedia format
        for pre in response.css("pre"):
            code_text = "".join(pre.css("::text").getall()).strip()
            if code_text:
                lang = ContentProcessor.detect_language(code_text) or "asm"
                item["code_blocks"].append({"lang": lang, "code": code_text})

        item["scraped_at"] = time.strftime("%Y-%m-%d")
        if last_modified:
            item["last_modified"] = last_modified

        yield item
