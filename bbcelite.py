"""
Spider Scrapy per elite.bbcelite.com.

Esegue un crawl limitato ad alcune sezioni del sito (about_site, deep_dives,
c64/indexes, hacks di default), estrae il contenuto principale di ogni pagina
con trafilatura (esclude nav/menu/footer) e lo converte in Markdown.

Uso:
    scrapy crawl bbcelite -a sections="about_site,deep_dives,c64/indexes,hacks" \
        -s DOCS_OUTPUT_DIR=docs_bbcelite

Parametri (-a):
    sections   Lista separata da virgole dei prefissi di path da includere nel crawl.
"""

import re
import time
from urllib.parse import urlparse

import trafilatura
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from ..items import DocItem

DEFAULT_SECTIONS = "about_site,deep_dives,c64/indexes,hacks"

KEYWORD_TAG_MAP = {
    "sound": "sid", "music": "sid", "maths": "math", "sprite": "graphics",
    "drawing": "graphics", "keyboard": "input", "joystick": "input",
    "memory_map": "memory", "index": "reference",
}


class BBCEliteSpider(CrawlSpider):
    name = "bbcelite"
    allowed_domains = ["elite.bbcelite.com"]

    def __init__(self, sections=DEFAULT_SECTIONS, *args, **kwargs):
        self.sections = [s.strip().strip("/") for s in sections.split(",") if s.strip()]
        self.start_urls = [f"https://elite.bbcelite.com/{s}/" for s in self.sections]

        # Segue solo i link il cui path inizia con una delle sezioni richieste,
        # restando così dentro al perimetro del tutorial (niente pagine di
        # copyright/licenza/altre piattaforme non richieste).
        allow_patterns = [rf"^https://elite\.bbcelite\.com/{re.escape(s)}/" for s in self.sections]

        self.rules = (
            Rule(LinkExtractor(allow=allow_patterns, deny=[r"\.(pdf|zip|jpg|png|gif)$"]),
                 callback="parse_item", follow=True),
        )

        super().__init__(*args, **kwargs)
        self._compile_rules()

    def parse_item(self, response):
        if "text/html" not in response.headers.get("Content-Type", b"").decode(errors="ignore"):
            return

        html = response.text
        raw_title = response.css("title::text").get() or response.url
        title = raw_title.split(" - Elite")[0].strip()

        body_md = trafilatura.extract(
            html,
            url=response.url,
            output_format="markdown",
            include_links=True,
            include_images=True,
            include_tables=True,
            favor_recall=True,
        )

        item = DocItem()
        item["url"] = response.url
        item["title"] = title
        item["category"] = self._category_from_url(response.url)
        item["tags"] = self._guess_tags(response.url)
        item["body_md"] = body_md
        item["scraped_at"] = time.strftime("%Y-%m-%d")
        yield item

    @staticmethod
    def _category_from_url(url: str) -> str:
        parts = [p for p in urlparse(url).path.strip("/").split("/") if p]
        if not parts:
            return "home"
        return "/".join(parts[:-1]) if len(parts) > 1 else parts[0]

    @staticmethod
    def _guess_tags(url: str) -> list:
        tags = ["c64" if "c64" in url or "commodore_64" in url else "6502"]
        for keyword, tag in KEYWORD_TAG_MAP.items():
            if keyword in url:
                tags.append(tag)
        return sorted(set(tags))
