#!/usr/bin/env python3
"""
build_pdf.py — Concatena i file Markdown (con opzioni di filtraggio tematico) e produce un PDF unico.

Richiede pandoc installato a livello di sistema:
    apt install pandoc texlive-xetex texlive-fonts-recommended    # Linux
    brew install pandoc basictex                                   # macOS

Uso:
    python build_pdf.py --docs docs_c64 --out manuale.pdf \
        --title "Elite 6502: Manuale Assembly per Commodore 64" \
        --author "Raccolta da elite.bbcelite.com (Mark Moxon)"
"""

import argparse
import pathlib
import re

import yaml
import pypandoc


def read_frontmatter(md_path: pathlib.Path) -> dict:
    try:
        text = md_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return {}
        _, fm, _ = text.split("---", 2)
        return yaml.safe_load(fm) or {}
    except (ValueError, OSError, yaml.YAMLError):
        return {}


def extract_links_in_order(index_md: pathlib.Path) -> list:
    text = index_md.read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)]+\.md)\)", text)
    seen, ordered = set(), []
    for link in links:
        if link not in seen:
            seen.add(link)
            ordered.append(link)
    return ordered


def strip_frontmatter(md_text: str) -> str:
    if md_text.startswith("---"):
        parts = md_text.split("---", 2)
        if len(parts) == 3:
            return parts[2].lstrip()
    return md_text


def concat_markdown(docs_dir: pathlib.Path, ordered_links: list) -> str:
    chunks = []
    for link in ordered_links:
        md_path = docs_dir / link
        if not md_path.exists():
            print(f"[attenzione] file mancante, saltato: {link}")
            continue
        text = strip_frontmatter(md_path.read_text(encoding="utf-8"))
        chunks.append(text)
    return "\n\n\\newpage\n\n".join(chunks)


def build_pdf(docs_dir: pathlib.Path, out_pdf: pathlib.Path, title: str, author: str,
              category_filter: str = None, topic_filter: str = None, hardware_filter: str = None):

    use_filters = category_filter or topic_filter or hardware_filter

    if use_filters:
        print(f"[info] Generazione PDF tematico con filtri:")
        if category_filter:
            print(f"  - Categoria: {category_filter}")
        if topic_filter:
            print(f"  - Argomento: {topic_filter}")
        if hardware_filter:
            print(f"  - Hardware: {hardware_filter}")

        ordered_links = []
        for p in sorted(docs_dir.rglob("*.md")):
            if p.name in ["index.md", "_combined.md"]:
                continue
            fm = read_frontmatter(p)
            if not fm:
                continue

            if category_filter and fm.get("category", "").lower() != category_filter.lower():
                continue
            if topic_filter and topic_filter.lower() not in [t.lower() for t in fm.get("topics", [])]:
                continue
            if hardware_filter and hardware_filter.lower() not in [h.lower() for h in fm.get("hardware", [])]:
                continue

            ordered_links.append(p.relative_to(docs_dir).as_posix())
    else:
        index_md = docs_dir / "index.md"
        if index_md.exists():
            ordered_links = extract_links_in_order(index_md)
        else:
            print("[info] index.md non trovato, uso l'ordine alfabetico dei file .md")
            ordered_links = [p.relative_to(docs_dir).as_posix() for p in sorted(docs_dir.rglob("*.md")) if p.name != "index.md"]

    if not ordered_links:
        print("[errore] nessun file markdown corrispondente ai criteri trovato.")
        return

    full_md = concat_markdown(docs_dir, ordered_links)

    combined_path = docs_dir / "_combined.md"
    combined_path.write_text(full_md, encoding="utf-8")

    extra_args = [
        "--toc",
        "--toc-depth=2",
        "--pdf-engine=xelatex",
        "-V", f"title={title}",
        "-V", f"author={author}",
        "-V", "geometry:margin=2.5cm",
        "-V", "mainfont=DejaVu Serif",
        "-V", "monofont=DejaVu Sans Mono",
        "-V", "CJKmainfont=DejaVu Sans", # Supporto per caratteri estesi
        "--highlight-style=tango",
        "--listings", # Usa il pacchetto listings per il codice
    ]

    try:
        pypandoc.convert_file(
            str(combined_path),
            to="pdf",
            outputfile=str(out_pdf),
            extra_args=extra_args,
        )
        print(f"PDF generato: {out_pdf}")
    except Exception as e:
        print(f"Errore pypandoc: {e}")
        print("Si prega di verificare che pandoc e xelatex siano installati nel sistema.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", default="docs_c64")
    parser.add_argument("--out", default="manuale_c64.pdf")
    parser.add_argument("--title", default="Elite 6502: Manuale di programmazione Assembly per Commodore 64")
    parser.add_argument("--author", default="Raccolta da elite.bbcelite.com (Mark Moxon)")
    parser.add_argument("--category", default=None, help="Filtra per categoria (es. tutorial, reference)")
    parser.add_argument("--topic", default=None, help="Filtra per argomento (es. raster interrupts, graphics)")
    parser.add_argument("--hardware", default=None, help="Filtra per hardware (es. VIC-II, SID)")
    args = parser.parse_args()

    build_pdf(
        pathlib.Path(args.docs),
        pathlib.Path(args.out),
        args.title,
        args.author,
        category_filter=args.category,
        topic_filter=args.topic,
        hardware_filter=args.hardware
    )


if __name__ == "__main__":
    main()
