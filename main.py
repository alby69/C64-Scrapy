#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path
from build_index import build_index
from build_pdf import build_pdf

def run_scrapy(spider, output_dir, extra_args=None):
    print(f"--- Avvio scraping: {spider} ---")
    cmd = ["scrapy", "crawl", spider, "-s", f"DOCS_OUTPUT_DIR={output_dir}"]
    if extra_args:
        cmd.extend(extra_args)
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser(description="C64 Scraper CLI")
    parser.add_argument("spider", nargs="?", help="Nome dello spider da eseguire (es. bbcelite, codebase64)")
    parser.add_argument("--output", default="docs_c64", help="Cartella di output")
    parser.add_argument("--index", action="store_true", help="Genera l'indice dopo lo scraping")
    parser.add_argument("--pdf", action="store_true", help="Genera il PDF dopo lo scraping")
    parser.add_argument("--all", action="store_true", help="Esegue tutti gli spider definiti")

    args, unknown = parser.parse_known_args()

    spiders = [args.spider] if args.spider else []
    if args.all:
        spiders = ["bbcelite", "codebase64"]

    if not spiders and not (args.index or args.pdf):
        parser.print_help()
        return

    for spider in spiders:
        try:
            run_scrapy(spider, args.output, unknown)
        except Exception as e:
            print(f"Errore durante lo scraping di {spider}: {e}")

    if args.index or args.all:
        print("--- Generazione Indice ---")
        build_index(Path(args.output))

    if args.pdf:
        print("--- Generazione PDF ---")
        try:
            build_pdf(Path(args.output), Path("manuale_c64.pdf"), "C64 Programming Manual", "C64 Intelligence SDK")
        except Exception as e:
            print(f"Errore generazione PDF: {e}. Assicurati che pandoc sia installato.")

if __name__ == "__main__":
    main()
