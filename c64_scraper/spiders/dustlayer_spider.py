import time
import scrapy
from scrapy import signals
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from c64_scraper.items import DocItem
from c64_scraper.utils.processor import ContentProcessor
from c64_scraper.utils.incremental_manager import IncrementalStateManager
from c64_scraper.utils.reporter import RunReporter

class DustlayerSpider(CrawlSpider):
    name = "dustlayer"
    allowed_domains = ["dustlayer.com"]
    start_urls = ["https://dustlayer.com/about"]

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

    def __init__(self, incremental: str = "false", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.incremental = str(incremental).lower() in ("true", "1", "yes")
        self.state_manager = IncrementalStateManager()
        self.reporter = RunReporter()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        self.state_manager.save_state(self.name)
        self.reporter.generate_report(self.name)
        self.logger.info("Saved incremental state and generated run report.")

    def parse_item(self, response):
        if "text/html" not in response.headers.get("Content-Type", b"").decode(errors="ignore"):
            return

        last_mod_header = response.headers.get("Last-Modified")
        last_modified = last_mod_header.decode("utf-8", errors="ignore") if last_mod_header else None

        if self.incremental and last_modified:
            if self.state_manager.is_page_unmodified(self.name, response.url, last_modified):
                self.logger.info(f"Skipping unmodified page: {response.url}")
                self.reporter.record_skipped(response.url)
                return

        html = response.text
        title = (response.css("h1::text").get() or response.css("title::text").get() or response.url).strip()

        body_md = ContentProcessor.extract_markdown(html, response.url)

        item = DocItem()
        item["url"] = response.url
        item["title"] = title
        item["category"] = "dustlayer"
        item["tags"] = ["c64", "tutorial", "assembly", "VIC-II"]
        item["body_md"] = body_md
        item["code_blocks"] = []

        for pre in response.css("pre, code"):
            code_text = "".join(pre.css("::text").getall()).strip()
            if code_text:
                lang = ContentProcessor.detect_language(code_text) or "asm"
                dialect = ContentProcessor.detect_assembly_dialect(code_text) if lang == "asm" else ""
                syntax_val = ContentProcessor.validate_code_syntax(code_text, lang)

                item["code_blocks"].append({
                    "lang": lang,
                    "dialect": dialect,
                    "code": code_text,
                    "syntax_valid": syntax_val["is_valid"],
                    "syntax_ratio": syntax_val["valid_ratio"]
                })

        item["scraped_at"] = time.strftime("%Y-%m-%d")
        if last_modified:
            item["last_modified"] = last_modified

        self.state_manager.update_page_state(self.name, response.url, last_modified, item["scraped_at"])
        self.reporter.record_scraped(response.url)

        yield item
