#!/usr/bin/env python3
import pathlib
import json
import re
import yaml
from c64_scraper.utils.processor import ContentProcessor

def read_frontmatter_and_body(md_path: pathlib.Path):
    try:
        text = md_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return {}, text
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return yaml.safe_load(parts[1]) or {}, parts[2]
        return {}, text
    except Exception:
        return {}, ""

def extract_code_blocks_from_md(md_text: str) -> list:
    """Extracts raw code blocks and their language from markdown."""
    pattern = r"```([a-zA-Z0-9_\-+]*)\n(.*?)\n```"
    blocks = []
    for match in re.finditer(pattern, md_text, re.DOTALL):
        lang = match.group(1).strip()
        code = match.group(2).strip()
        blocks.append({"lang": lang, "code": code})
    return blocks

def build_api_index(docs_dir: pathlib.Path, output_json: pathlib.Path):
    if not docs_dir.exists():
        print(f"[avviso] la cartella {docs_dir} non esiste. Impossibile creare l'API index.")
        return

    pages = []

    for md_path in sorted(docs_dir.rglob("*.md")):
        if md_path.name in ["index.md", "_combined.md"]:
            continue

        fm, body = read_frontmatter_and_body(md_path)
        if not fm:
            continue

        url = fm.get("source_url", "")
        code_blocks = extract_code_blocks_from_md(body)

        snippets = []
        all_routines = []

        for block in code_blocks:
            code_text = block["code"]
            lang = block["lang"]

            dialect = "BASIC"
            if lang in ["asm", "assembly"]:
                dialect = ContentProcessor.detect_assembly_dialect(code_text)
                routines = ContentProcessor.extract_routines_from_code(code_text, url)
                all_routines.extend(routines)

            snippets.append({
                "language": "assembly" if lang in ["asm", "assembly"] else "basic",
                "dialect": dialect,
                "code": code_text
            })

        page_entry = {
            "filepath": md_path.relative_to(docs_dir).as_posix(),
            "title": fm.get("title", md_path.stem),
            "source_url": url,
            "category": fm.get("category", "reference"),
            "topics": fm.get("topics", []),
            "difficulty": fm.get("difficulty", "intermediate"),
            "language": fm.get("language", "none"),
            "hardware": fm.get("hardware", []),
            "related": fm.get("related", []),
            "code_snippets": snippets,
            "routines": all_routines
        }
        pages.append(page_entry)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(pages, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"JSON API Index generato con successo: {output_json} ({len(pages)} pagine indicizzate)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Costruisce l'indice JSON API")
    parser.add_argument("--docs", default="docs_c64", help="Cartella con i file Markdown")
    parser.add_argument("--out", default="dataset_c64/api_index.json", help="File JSON di output")
    args = parser.parse_args()
    build_api_index(pathlib.Path(args.docs), pathlib.Path(args.out))
