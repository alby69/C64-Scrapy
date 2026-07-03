import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import time
from c64_scraper.items import DocItem
from c64_scraper.utils.processor import ContentProcessor

class Codebase64Spider(CrawlSpider):
    name = "codebase64"
    allowed_domains = ["codebase64.org"]
    start_urls = ["https://codebase64.org/doku.php?id=start"]

    rules = (
        Rule(LinkExtractor(allow=(r"id=mag:", r"id=base:", r"id=programming:")), callback="parse_item", follow=True),
    )

    def parse_item(self, response):
        html = response.text
        title = (response.css("h1::text").get() or response.url).strip()

        body_md = ContentProcessor.extract_markdown(html, response.url)

        item = DocItem()
        item["url"] = response.url
        item["title"] = title.strip()
        item["category"] = "codebase64"
        item["tags"] = ["c64", "codebase64", "assembly"]
        item["body_md"] = body_md
        item["code_blocks"] = [] # Da implementare specificamente per DokuWiki
        item["scraped_at"] = time.strftime("%Y-%m-%d")
        yield item
