import re
import time
from urllib.parse import urlparse

import scrapy
from scrapy import signals
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from c64_scraper.items import DocItem
from c64_scraper.utils.processor import ContentProcessor
from c64_scraper.utils.incremental_manager import IncrementalStateManager
from c64_scraper.utils.reporter import RunReporter

DEFAULT_SECTIONS = "about_site,deep_dives,c64/indexes,hacks"

KEYWORD_TAG_MAP = {
    "sound": "sid", "music": "sid", "maths": "math", "sprite": "graphics",
    "drawing": "graphics", "keyboard": "input", "joystick": "input",
    "memory_map": "memory", "index": "reference",
}

class BBCEliteSpider(CrawlSpider):
    name = "bbcelite"
    allowed_domains = ["elite.bbcelite.com"]

    def __init__(self, sections=DEFAULT_SECTIONS, incremental: str = "false", *args, **kwargs):
        self.sections = [s.strip().strip("/") for s in sections.split(",") if s.strip()]
        self.start_urls = [f"https://elite.bbcelite.com/{s}/" for s in self.sections]
        self.incremental = str(incremental).lower() in ("true", "1", "yes")

        allow_patterns = [rf"^https://elite\.bbcelite\.com/{re.escape(s)}/" for s in self.sections]

        self.rules = (
            Rule(LinkExtractor(allow=allow_patterns, deny=[r"\.(pdf|zip|jpg|png|gif)$"]),
                 callback="parse_item", follow=True),
        )

        super().__init__(*args, **kwargs)
        self._compile_rules()
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
        title = ContentProcessor.clean_title(response.css("title::text").get() or response.url, " - Elite")

        body_md = ContentProcessor.extract_markdown(html, response.url)

        item = DocItem()
        item["url"] = response.url
        item["title"] = title
        item["category"] = self._category_from_url(response.url)
        item["tags"] = self._guess_tags(response.url)
        item["body_md"] = body_md
        item["code_blocks"] = self._extract_explicit_code(response)
        item["scraped_at"] = time.strftime("%Y-%m-%d")
        if last_modified:
            item["last_modified"] = last_modified

        self.state_manager.update_page_state(self.name, response.url, last_modified, item["scraped_at"])
        self.reporter.record_scraped(response.url)

        yield item

    @staticmethod
    def _category_from_url(url: str) -> str:
        parts = [p for p in urlparse(url).path.strip("/").split("/") if p]
        if not parts:
            return "home"
        return "/".join(parts[:-1]) if len(parts) > 1 else parts[0]

    def _extract_explicit_code(self, response) -> list:
        blocks = []
        for pre in response.css("pre, code.code, div.code"):
            code_text = "".join(pre.css("::text").getall()).strip()
            if not code_text:
                continue

            lang = ContentProcessor.detect_language(code_text) or "asm"
            dialect = ContentProcessor.detect_assembly_dialect(code_text) if lang == "asm" else ""
            syntax_val = ContentProcessor.validate_code_syntax(code_text, lang)

            blocks.append({
                "lang": lang,
                "dialect": dialect,
                "code": code_text,
                "syntax_valid": syntax_val["is_valid"],
                "syntax_ratio": syntax_val["valid_ratio"]
            })
        return blocks

    @staticmethod
    def _guess_tags(url: str) -> list:
        tags = ["c64" if "c64" in url or "commodore_64" in url else "6502"]
        for keyword, tag in KEYWORD_TAG_MAP.items():
            if keyword in url:
                tags.append(tag)
        return sorted(set(tags))
