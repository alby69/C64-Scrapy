import json
import re
import time
import urllib.parse
import scrapy
from scrapy import signals
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from c64_scraper.items import DocItem
from c64_scraper.utils.processor import ContentProcessor
from c64_scraper.utils.code_lang_detector import CodeLanguageDetector
from c64_scraper.utils.incremental_manager import IncrementalStateManager
from c64_scraper.utils.reporter import RunReporter

class C64WikiSpider(CrawlSpider):
    name = "c64wiki"
    allowed_domains = ["c64-wiki.com", "www.c64-wiki.com"]
    start_urls = [
        "https://www.c64-wiki.com/wiki/Portal:Programming",
        "https://www.c64-wiki.com/wiki/Special:AllPages"
    ]

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

    def __init__(self, incremental: str = "false", start_urls: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.incremental = str(incremental).lower() in ("true", "1", "yes")
        if start_urls:
            self.start_urls = [s.strip() for s in start_urls.split(",") if s.strip()]
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

        title_key = response.url.split("/wiki/")[-1].split("#")[0]
        title_key_decoded = urllib.parse.unquote(title_key).replace("_", " ")
        encoded_title = urllib.parse.quote(title_key_decoded)

        meta_url = f"https://www.c64-wiki.com/rest.php/v1/page/{encoded_title}"
        yield scrapy.Request(
            meta_url,
            callback=self.parse_rest_meta,
            errback=self.handle_rest_error,
            cb_kwargs={
                "page_url": response.url,
                "title_key_decoded": title_key_decoded,
                "fallback_html": response.text,
                "fallback_last_modified": response.headers.get("Last-Modified", b"").decode("utf-8", errors="ignore")
            }
        )

    def parse_rest_meta(self, response, page_url, title_key_decoded, fallback_html, fallback_last_modified):
        meta = {}
        try:
            meta = json.loads(response.text)
        except Exception:
            pass

        last_modified = meta.get("latest", {}).get("timestamp") or fallback_last_modified or None

        if self.incremental and last_modified:
            if self.state_manager.is_page_unmodified(self.name, page_url, last_modified):
                self.logger.info(f"Skipping unmodified page: {page_url}")
                self.reporter.record_skipped(page_url)
                return

        encoded_title = urllib.parse.quote(title_key_decoded)
        html_url = f"https://www.c64-wiki.com/rest.php/v1/page/{encoded_title}/html"

        yield scrapy.Request(
            html_url,
            callback=self.parse_rest_html,
            errback=self.handle_rest_error,
            cb_kwargs={
                "page_url": page_url,
                "title_key_decoded": title_key_decoded,
                "rest_meta": meta,
                "fallback_html": fallback_html,
                "last_modified": last_modified
            }
        )

    def parse_rest_html(self, response, page_url, title_key_decoded, rest_meta, fallback_html, last_modified):
        rest_html = response.text if response.status == 200 else None

        if rest_meta and rest_html:
            title = rest_meta.get("title") or title_key_decoded
            body_md = ContentProcessor.extract_markdown(rest_html, page_url)
            wiki_revision_id = rest_meta.get("latest", {}).get("id")
            license_info = rest_meta.get("license", {}).get("title", "GFDL")
            html_for_code = rest_html
        else:
            title = ContentProcessor.clean_title(title_key_decoded, " - C64-Wiki")
            body_md = ContentProcessor.extract_markdown(fallback_html, page_url)
            wiki_revision_id = None
            license_info = "GFDL"
            html_for_code = fallback_html

        enriched = ContentProcessor.classify_document(html_for_code, body_md, page_url, title, spider_name=self.name)

        item = DocItem()
        item["url"] = page_url
        item["title"] = title
        item["category"] = enriched.get("category", "c64wiki")
        item["tags"] = list(set(["c64", "wiki", "reference"] + enriched.get("topics", [])))
        item["body_md"] = body_md
        item["code_blocks"] = []

        sel = scrapy.Selector(text=html_for_code)
        for pre in sel.css("pre, div.mw-highlight"):
            code_text = "".join(pre.css("::text").getall()).strip()
            if code_text:
                lang_class = pre.attrib.get("class", "")
                lang_hint = ""
                if "mw-highlight" in lang_class or "lang-" in lang_class:
                    m = re.search(r'lang-([a-zA-Z0-9_-]+)', lang_class)
                    if m:
                        lang_hint = m.group(1)

                lang = CodeLanguageDetector.detect_language(code_text, hint=lang_hint)
                dialect = CodeLanguageDetector.detect_assembly_dialect(code_text) if lang == "asm" else ""

                item["code_blocks"].append({
                    "lang": lang,
                    "dialect": dialect,
                    "code": code_text
                })

        item["scraped_at"] = time.strftime("%Y-%m-%d")
        if last_modified:
            item["last_modified"] = last_modified
        item["license"] = license_info
        if wiki_revision_id:
            item["wiki_revision_id"] = wiki_revision_id

        item["topics"] = enriched.get("topics", [])
        item["difficulty"] = enriched.get("difficulty", "intermediate")
        item["language"] = enriched.get("language", "none")
        item["hardware"] = enriched.get("hardware", [])
        item["related"] = enriched.get("related", [])

        self.state_manager.update_page_state(self.name, page_url, last_modified, item["scraped_at"])
        self.reporter.record_scraped(page_url)

        yield item

    def handle_rest_error(self, failure):
        request = failure.request
        page_url = request.cb_kwargs.get("page_url", request.url)
        self.reporter.record_error(page_url, str(failure.value))
        self.logger.warning(f"REST API request failed for {page_url}: {failure.value}")
