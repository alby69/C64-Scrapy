import hashlib
import json
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
        self.out_dir = pathlib.Path(spider.settings.get("DOCS_OUTPUT_DIR", "docs_c64"))
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter["url"]

        domain = urlparse(url).netloc.replace(".", "_")
        file_path = self.out_dir / domain / self._slugify_path(url)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        frontmatter = {
            "title": adapter["title"],
            "source_url": url,
            "category": adapter["category"],
            "tags": adapter["tags"],
            "scraped_at": adapter["scraped_at"],
        }
        if "last_modified" in adapter and adapter["last_modified"]:
            frontmatter["last_modified"] = adapter["last_modified"]

        content = "---\n" + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n\n"
        content += f"# {adapter['title']}\n\n"
        content += adapter["body_md"] or "*(contenuto non estratto automaticamente — controllare l'URL sorgente)*\n"

        if adapter.get("code_blocks"):
            content += "\n\n## Codice Estratto\n\n"
            for block in adapter["code_blocks"]:
                lang = block.get("lang", "")
                code = block.get("code", "")
                content += f"```{lang}\n{code}\n```\n\n"

        content += f"\n\n---\n*Fonte originale: [{url}]({url})*\n"

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


class JsonDatasetPipeline:
    """Converte DocItem in righe JSONL compatibili con build_dataset.py dell'SDK."""

    def open_spider(self, spider):
        self.out_dir = pathlib.Path(spider.settings.get("DATASET_OUTPUT_DIR", "dataset_c64"))
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.file = open(self.out_dir / "scraped_dataset.jsonl", "a", encoding="utf-8")

    def close_spider(self, spider):
        if hasattr(self, "file") and self.file:
            self.file.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter["url"]

        # Genera un ID deterministico basato su SHA256 per l'item
        unique_id = f"{spider.name}_{hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]}"

        record = {
            "id": unique_id,
            "text": f"{adapter['title']}\n\n{adapter['body_md'] or ''}",
            "metadata": {
                "source": url,
                "category": adapter["category"],
                "tags": adapter["tags"],
                "scraped_at": adapter["scraped_at"],
                "spider": spider.name
            }
        }
        if "last_modified" in adapter and adapter["last_modified"]:
            record["metadata"]["last_modified"] = adapter["last_modified"]

        self.file.write(json.dumps(record, ensure_ascii=False) + "\n")
        return item
