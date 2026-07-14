import hashlib
import json
import pathlib
import re
from urllib.parse import urlparse

import yaml
from itemadapter import ItemAdapter

from c64_scraper.utils.processor import ContentProcessor


class MarkdownWriterPipeline:
    """Converte ogni DocItem in un file .md con frontmatter YAML arricchito,
    rispecchiando la struttura di path del sito sorgente."""

    def open_spider(self, spider):
        self.out_dir = pathlib.Path(spider.settings.get("DOCS_OUTPUT_DIR", "docs_c64"))
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter["url"]

        domain = urlparse(url).netloc.replace(".", "_")
        file_path = self.out_dir / domain / self._slugify_path(url)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Esegui classificazione semantica avanzata
        classification = ContentProcessor.classify_document(
            "", adapter.get("body_md", ""), url, adapter["title"], spider.name
        )

        frontmatter = {
            "title": adapter["title"],
            "source_url": url,
            "category": classification["category"],
            "topics": classification["topics"],
            "difficulty": classification["difficulty"],
            "language": classification["language"],
            "hardware": classification["hardware"],
            "related": classification["related"],
            "scraped_at": adapter["scraped_at"],
        }
        if "last_modified" in adapter and adapter["last_modified"]:
            frontmatter["last_modified"] = adapter["last_modified"]

        content = "---\n" + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n\n"
        content += f"# {adapter['title']}\n\n"
        content += adapter["body_md"] or "*(contenuto non estratto automaticamente — controllare l'URL sorgente)*\n"

        code_blocks = adapter.get("code_blocks", [])
        if code_blocks:
            content += "\n\n## Codice Estratto\n\n"
            for block in code_blocks:
                code_text = block.get("code", "")
                lang = block.get("lang", "")

                # Rileva dialetto e routine
                if lang in ["asm", "assembly"]:
                    dialect = ContentProcessor.detect_assembly_dialect(code_text)
                    routines = ContentProcessor.extract_routines_from_code(code_text, url)
                    content += f"### Snippet Codice (Dialetto: {dialect})\n\n"

                    if routines:
                        content += "#### Routine Identificate:\n"
                        for r in routines:
                            content += f"- **`{r['name']}`** ({r['address']}): {r['description']}\n"
                        content += "\n"

                    content += f"```assembly\n{code_text}\n```\n\n"
                else:
                    content += f"### Snippet Codice (BASIC)\n\n"
                    content += f"```basic\n{code_text}\n```\n\n"

        content += f"\n\n---\n*Fonte originale: [{url}]({url})*\n"

        file_path.write_text(content, encoding="utf-8")
        spider.logger.info("Salvato: %s", file_path)
        return item

    @staticmethod
    def _slugify_path(url: str) -> pathlib.Path:
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if not path or path == "index.html" or path == "cbmdocs.html":
            return pathlib.Path("index.md")

        script_ext = re.compile(r"\.(php|cgi|asp|aspx|jsp)$", re.IGNORECASE)
        if script_ext.search(path):
            from urllib.parse import parse_qs
            qs = parse_qs(parsed.query)
            page_id = qs.get("id", [None])[0]
            if page_id:
                path = re.sub(r"[^a-zA-Z0-9/_-]", "_", page_id.replace(":", "/"))
            else:
                path = script_ext.sub("", path)

        path = re.sub(r"\.html?$", "", path)
        return pathlib.Path(path + ".md")


class JsonDatasetPipeline:
    """Converte DocItem in righe JSONL arricchite con classificazione semantica."""

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

        classification = ContentProcessor.classify_document(
            "", adapter.get("body_md", ""), url, adapter["title"], spider.name
        )

        record = {
            "id": unique_id,
            "text": f"{adapter['title']}\n\n{adapter['body_md'] or ''}",
            "metadata": {
                "source": url,
                "category": classification["category"],
                "topics": classification["topics"],
                "difficulty": classification["difficulty"],
                "language": classification["language"],
                "hardware": classification["hardware"],
                "related": classification["related"],
                "scraped_at": adapter["scraped_at"],
                "spider": spider.name
            }
        }
        if "last_modified" in adapter and adapter["last_modified"]:
            record["metadata"]["last_modified"] = adapter["last_modified"]

        self.file.write(json.dumps(record, ensure_ascii=False) + "\n")
        return item
