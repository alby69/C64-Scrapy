#!/usr/bin/env python3
"""
build_pdf.py — Concatena i file Markdown (nell'ordine di index.md) e produce un PDF unico.

Richiede pandoc installato a livello di sistema:
    apt install pandoc texlive-xetex texlive-fonts-recommended    # Linux
    brew install pandoc basictex                                   # macOS

Uso:
    python build_pdf.py --docs docs_bbcelite --out manuale.pdf \
        --title "Elite 6502: Manuale Assembly per Commodore 64" \
        --author "Raccolta da elite.bbcelite.com (Mark Moxon)"
"""

import argparse
import pathlib
import re

import pypandoc


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


def build_pdf(docs_dir: pathlib.Path, out_pdf: pathlib.Path, title: str, author: str):
    index_md = docs_dir / "index.md"
    if not index_md.exists():
        raise SystemExit("index.md non trovato: esegui prima build_index.py")

    ordered_links = extract_links_in_order(index_md)
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
        "--highlight-style=tango",
    ]

    pypandoc.convert_file(
        str(combined_path),
        to="pdf",
        outputfile=str(out_pdf),
        extra_args=extra_args,
    )
    print(f"PDF generato: {out_pdf}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", default="docs_bbcelite")
    parser.add_argument("--out", default="manuale_c64_elite.pdf")
    parser.add_argument("--title", default="Elite 6502: Manuale di programmazione Assembly per Commodore 64")
    parser.add_argument("--author", default="Raccolta da elite.bbcelite.com (Mark Moxon)")
    args = parser.parse_args()

    build_pdf(pathlib.Path(args.docs), pathlib.Path(args.out), args.title, args.author)


if __name__ == "__main__":
    main()
