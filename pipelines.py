import pathlib
import re
from urllib.parse import urlparse

import yaml
from itemadapter import ItemAdapter


class MarkdownWriterPipeline:
    """Converte ogni DocItem in un file .md con frontmatter YAML, rispecchiando
    la struttura di path del sito sorgente (es. /deep_dives/maths/foo.html ->
    deep_dives/maths/foo.md)."""

    def open_spider(self, spider):
        self.out_dir = pathlib.Path(spider.settings.get("DOCS_OUTPUT_DIR", "docs_bbcelite"))
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter["url"]

        file_path = self.out_dir / self._slugify_path(url)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        frontmatter = {
            "title": adapter["title"],
            "source_url": url,
            "category": adapter["category"],
            "tags": adapter["tags"],
            "scraped_at": adapter["scraped_at"],
        }
        content = "---\n" + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n\n"
        content += f"# {adapter['title']}\n\n"
        content += adapter["body_md"] or "*(contenuto non estratto automaticamente — controllare l'URL sorgente)*\n"
        content += f"\n\n---\n*Fonte originale: [{url}]({url}) — © Mark Moxon / I. Bell / D. Braben.*\n"

        file_path.write_text(content, encoding="utf-8")
        spider.logger.info("Salvato: %s", file_path)
        return item

    @staticmethod
    def _slugify_path(url: str) -> pathlib.Path:
        path = urlparse(url).path.strip("/")
        if not path or path == "index.html":
            return pathlib.Path("index.md")
        path = re.sub(r"\.html?$", "", path)
        return pathlib.Path(path + ".md")
