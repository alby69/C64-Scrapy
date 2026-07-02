#!/usr/bin/env python3
"""
build_index.py — Genera index.md leggendo il frontmatter di tutti i file .md
prodotti dallo spider Scrapy (bbcelite_scraper/pipelines.py).

Uso:
    python build_index.py --docs docs_bbcelite
"""

import argparse
import collections
import pathlib

import yaml


def read_frontmatter(md_path: pathlib.Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    try:
        _, fm, _ = text.split("---", 2)
        return yaml.safe_load(fm) or {}
    except ValueError:
        return {}


def build_index(docs_dir: pathlib.Path):
    by_category = collections.defaultdict(list)

    for md_path in sorted(docs_dir.rglob("*.md")):
        if md_path.name == "index.md":
            continue
        fm = read_frontmatter(md_path)
        if not fm:
            continue
        category = fm.get("category", "varie")
        rel_link = md_path.relative_to(docs_dir).as_posix()
        by_category[category].append((fm.get("title", md_path.stem), rel_link))

    lines = [
        "# Indice — Manuale di programmazione Assembly 6502 per Commodore 64",
        "",
        "> Documentazione estratta da [elite.bbcelite.com](https://elite.bbcelite.com/), "
        "a cura di Mark Moxon. Uso educativo personale.",
        "",
    ]

    for category in sorted(by_category):
        lines.append(f"## {category}")
        lines.append("")
        for title, link in sorted(by_category[category]):
            lines.append(f"- [{title}]({link})")
        lines.append("")

    index_path = docs_dir / "index.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Indice generato: {index_path} ({sum(len(v) for v in by_category.values())} pagine, "
          f"{len(by_category)} categorie)")
    return index_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", default="docs_bbcelite", help="Cartella con i file Markdown")
    args = parser.parse_args()
    build_index(pathlib.Path(args.docs))


if __name__ == "__main__":
    main()
