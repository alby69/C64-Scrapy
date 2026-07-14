import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import time
from c64_scraper.items import DocItem
from c64_scraper.utils.processor import ContentProcessor


def _normalize_dokuwiki_links(links):
    seen_ids = set()
    normalized = []
    for link in links:
        parsed = urlparse(link.url)
        qs = parse_qs(parsed.query)
        page_id = qs.get("id", [None])[0]
        if page_id is None:
            continue
        if page_id in seen_ids:
            continue
        seen_ids.add(page_id)
        link.url = urlunparse(parsed._replace(query=urlencode({"id": page_id})))
        normalized.append(link)
    return normalized


class Codebase64Spider(CrawlSpider):
    name = "codebase64"
    allowed_domains = ["codebase.c64.org"]
    start_urls = ["https://codebase.c64.org/doku.php?id=start"]
    custom_settings = {
        "CLOSESPIDER_PAGECOUNT": 500,
    }

    rules = (
        Rule(
            LinkExtractor(allow=(r"id=mag:", r"id=base:", r"id=programming:")),
            callback="parse_item",
            follow=True,
            process_links=_normalize_dokuwiki_links,
        ),
    )

    def parse_item(self, response):
        if "text/html" not in response.headers.get("Content-Type", b"").decode(errors="ignore"):
            return

        html = response.text
        title = (response.css("h1::text").get() or response.css("title::text").get() or response.url).strip()

        body_md = ContentProcessor.extract_markdown(html, response.url)

        # Get last modified header if present
        last_mod_header = response.headers.get("Last-Modified")
        last_modified = last_mod_header.decode("utf-8", errors="ignore") if last_mod_header else None

        item = DocItem()
        item["url"] = response.url
        item["title"] = title.strip()
        item["category"] = "codebase64"
        item["tags"] = ["c64", "codebase64", "assembly"]
        item["body_md"] = body_md
        item["code_blocks"] = []

        # Extract code blocks from DokuWiki format (pre.code)
        for pre in response.css("pre.code"):
            code_text = "".join(pre.css("::text").getall()).strip()
            if code_text:
                lang = ContentProcessor.detect_language(code_text) or "asm"
                item["code_blocks"].append({"lang": lang, "code": code_text})

        item["scraped_at"] = time.strftime("%Y-%m-%d")
        if last_modified:
            item["last_modified"] = last_modified
        yield item
