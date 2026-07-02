import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import trafilatura
import time
from ..items import DocItem

class Codebase64Spider(CrawlSpider):
    name = "codebase64"
    allowed_domains = ["codebase64.org"]
    start_urls = ["https://codebase64.org/doku.php?id=start"]

    rules = (
        Rule(LinkExtractor(allow=(r"id=mag:", r"id=base:", r"id=programming:")), callback="parse_item", follow=True),
    )

    def parse_item(self, response):
        html = response.text
        title = response.css("h1::text").get() or response.url

        body_md = trafilatura.extract(
            html,
            url=response.url,
            output_format="markdown",
            include_links=True,
            include_images=True,
            include_tables=True,
        )

        item = DocItem()
        item["url"] = response.url
        item["title"] = title.strip()
        item["category"] = "codebase64"
        item["tags"] = ["c64", "codebase64", "assembly"]
        item["body_md"] = body_md
        item["code_blocks"] = [] # Da implementare specificamente per DokuWiki
        item["scraped_at"] = time.strftime("%Y-%m-%d")
        yield item
