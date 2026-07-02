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

        # Estrazione base con trafilatura
        body_md = trafilatura.extract(
            html,
            url=response.url,
            output_format="markdown",
            include_links=True,
            include_images=True,
            include_tables=True,
            favor_recall=True,
        )

        # Post-processing per migliorare l'estrazione del codice
        if body_md:
            body_md = self._improve_code_blocks(body_md, response)

        item = DocItem()
        item["url"] = response.url
        item["title"] = title
        item["category"] = self._category_from_url(response.url)
        item["tags"] = self._guess_tags(response.url)
        item["body_md"] = body_md
        item["code_blocks"] = self._extract_explicit_code(response)
        item["scraped_at"] = time.strftime("%Y-%m-%d")
        yield item

    @staticmethod
    def _category_from_url(url: str) -> str:
        parts = [p for p in urlparse(url).path.strip("/").split("/") if p]
        if not parts:
            return "home"
        return "/".join(parts[:-1]) if len(parts) > 1 else parts[0]

    def _extract_explicit_code(self, response) -> list:
        """Estrae blocchi di codice espliciti dai tag <pre> o <code>."""
        blocks = []
        # Cerchiamo blocchi che potrebbero essere assembly o basic
        for pre in response.css("pre, code.code, div.code"):
            code = pre.css("::text").getall()
            code_text = "".join(code).strip()
            if not code_text:
                continue

            lang = "asm" # Default per questo sito
            if any(k in code_text.lower() for k in ["print", "goto", "if", "then", "poke", "peek"]):
                lang = "basic"

            blocks.append({"lang": lang, "code": code_text})
        return blocks

    def _improve_code_blocks(self, content: str, response) -> str:
        """
        Migliora la formattazione dei blocchi di codice Assembly 6502.
        """
        asm_keywords = r"\b(LDA|STA|LDX|STX|LDY|STY|JSR|RTS|JMP|BEQ|BNE|CMP|CPX|CPY|INC|DEC|ADC|SBC|PHA|PLA|PHP|PLP|ASL|LSR|ROL|ROR|AND|ORA|EOR|BIT|SEC|CLC|SED|CLD|SEI|CLI|TAX|TXA|TAY|TYA|TSX|TXS)\b"

        # Esempio di post-processing per marcare blocchi di testo come assembly
        # se contengono istruzioni tipiche e non sono già formattati.
        # Per ora limitiamo l'intervento per evitare falsi positivi nel testo narrativo.

        return content

    @staticmethod
    def _guess_tags(url: str) -> list:
        tags = ["c64" if "c64" in url or "commodore_64" in url else "6502"]
        for keyword, tag in KEYWORD_TAG_MAP.items():
            if keyword in url:
                tags.append(tag)
        return sorted(set(tags))
